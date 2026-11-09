"""Real LiveKit SDK + real LLM, scripted synthetic users, unedited raw outputs.

No judge pass is invented: automatic checks are deliberately separate from the
human-readable expectations. Each run retains failures and timing.
"""

import argparse
import asyncio
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import AgentSession

from advocate.case import CaseState
from advocate.workflow import ConsultationAgent, make_llm

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env.local")


async def run(selected=None):
    scenarios = json.loads(
        (ROOT / "tests" / "consultations.json").read_text(encoding="utf-8")
    )
    directory = (
        ROOT / "test-results" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    directory.mkdir(parents=True)
    results = []
    for scenario in scenarios:
        if selected and scenario["id"] not in selected:
            continue
        state = CaseState(draft_directory=directory / "drafts")
        record = {
            "id": scenario["id"],
            "expectation": scenario["expectation"],
            "turns": [],
            "status": "running",
        }
        started = time.monotonic()
        session = None
        try:
            async with (
                make_llm() as model,
                AgentSession[CaseState](userdata=state) as session,
            ):
                await session.start(ConsultationAgent(model=model))
                for user_input in scenario["turns"]:
                    turn_start = time.monotonic()
                    result = await asyncio.wait_for(
                        session.run(user_input=user_input), timeout=100
                    )
                    events = [
                        {"type": event.type, "item": event.item.model_dump(mode="json")}
                        for event in result.events
                        if hasattr(event, "item")
                    ]
                    record["turns"].append(
                        {
                            "input": user_input,
                            "duration_seconds": time.monotonic() - turn_start,
                            "events": events,
                            "case": state.snapshot(),
                        }
                    )
                record["status"] = "completed_ungraded"
                # These assert state/effects, not the quality of natural language.
                if scenario["id"] == "confirmed_draft":
                    assert not record["turns"][0]["case"]["drafts"], (
                        "Draft created before later confirmation"
                    )
                    assert len(state.drafts) == 1, (
                        "No actual draft created after confirmation"
                    )
                    assert (
                        "8000" in state.drafts[0]["text"]
                        and "INR" in state.drafts[0]["text"]
                        and "Acme" in state.drafts[0]["text"]
                    )
                    assert (
                        "[Your name]" in state.drafts[0]["text"]
                        and "[Merchant address]" in state.drafts[0]["text"]
                    )
                if scenario["id"] == "rejected_draft":
                    assert not state.drafts, "Draft created despite refusal"
                if scenario["id"] == "contradictory_amount":
                    assert "amount" in record["turns"][1]["case"]["contradictions"], (
                        "Conflicting amount was silently overwritten"
                    )
                    assert "5000" in state.value("amount"), "Correction not retained"
                if scenario["id"] == "conditional_approval":
                    assert not state.drafts, "Conditional approval created a draft"
                if scenario["id"] == "correction_before_draft":
                    assert not record["turns"][1]["case"]["drafts"], (
                        "Drafted before re-reviewing corrected facts"
                    )
                    assert (
                        len(state.drafts) == 1 and "6000" in state.drafts[0]["text"]
                    ), "Corrected draft missing"
                    amount_line = next(
                        line
                        for line in state.drafts[0]["text"].splitlines()
                        if line.startswith("- Consideration paid as reported:")
                    )
                    assert "6000" in amount_line and "8000" not in amount_line, (
                        "Stale operative amount in draft"
                    )
                if scenario["id"] == "verified_options":
                    assert state.legal_receipts, "No source verification performed"
                if scenario["id"] == "argument_practice":
                    assert state.mode == "consultation", "Did not return from role-play"
                if scenario["id"] == "urgent_outside_scope":
                    assert state.risk == "urgent", (
                        "Urgency did not reach application state"
                    )
                record["structural_checks"] = "passed"
        except Exception:
            record["status"] = "failed"
            record["error"] = traceback.format_exc()
        finally:
            record["duration_seconds"] = time.monotonic() - started
            if session:
                record["history"] = session.history.to_dict(
                    exclude_timestamp=False, exclude_metrics=False
                )
            record["final_case"] = state.snapshot()
            record["interpretations"] = state.interpreted
            record["drafts"] = state.drafts
            (directory / f"{scenario['id']}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            results.append(
                {
                    "id": scenario["id"],
                    "status": record["status"],
                    "seconds": record["duration_seconds"],
                }
            )
            print(
                f"{scenario['id']}: {record['status']} ({record['duration_seconds']:.1f}s)",
                flush=True,
            )
    (directory / "summary.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(f"Raw results: {directory}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", action="append")
    args = parser.parse_args()
    results = asyncio.run(run(args.scenario))
    raise SystemExit(1 if any(item["status"] == "failed" for item in results) else 0)
