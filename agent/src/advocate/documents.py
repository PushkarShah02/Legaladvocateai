"""Templates never invent names, legal provisions, filing details, or evidence."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from advocate.case import CaseState, DocumentKind


def render_document(state: CaseState, kind: DocumentKind) -> str:
    if (
        not state.review
        or not state.review["approved"]
        or state.review["version"] != state.version
    ):
        raise ValueError("Confirmed current case review required.")
    v = state.value
    heading = (
        "Refund request / draft notice from consumer"
        if kind == "refund_request"
        else "Consumer complaint — preparation draft, not filed"
    )
    intro = (
        "Please review this consumer refund request and provide a written response."
        if kind == "refund_request"
        else "Before the appropriate Consumer Disputes Redressal Commission: [Forum and jurisdiction to be verified]."
    )
    facts = "\n".join(
        f"- {label}: {v(key)}"
        for key, label in [
            ("purchase", "Goods or services"),
            ("amount", "Consideration paid as reported"),
            ("purchase_date", "Purchase date"),
            ("problem_date", "Issue arose"),
            ("problem", "Problem described"),
            ("location", "Location"),
            ("purpose", "Purpose of purchase"),
            ("order_id", "Order/reference number"),
            ("contact_attempt", "Steps already taken"),
            ("merchant_response", "Merchant response"),
        ]
    )
    return f"""# {heading}

Date: {datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()}
From: {v("consumer_name", "[Your name]")}
Address: {v("consumer_address", "[Your address]")}
To: {v("merchant")}
Address: {v("merchant_address", "[Merchant address]")}

{intro}

## Statement of facts
The following is my account, subject to the supporting records. Disputed facts are not presented as adjudicated findings.

{facts}

Original user statement supporting the amount: {state.facts["amount"].quote if "amount" in state.facts else "[Amount and currency to be supplied]"}

## Requested resolution
{v("desired_outcome")}

## Evidence and enclosures
{v("evidence", "[List only documents actually available; do not claim unattached enclosures]")}
Evidence availability is reported by the consumer; the assistant has not inspected or authenticated documents.

## Response requested
{v("reply_by", "[Choose a reasonable requested response date; this is not a statutory deadline]")}
If unresolved, I may consider appropriate grievance-redressal options after checking eligibility and procedure.

Signature: {v("consumer_name", "[Your name]")}

---
PREPARATION DRAFT ONLY. Not sent, filed, or reviewed by a licensed advocate.
Replace every placeholder and check names, dates, amounts, service requirements, jurisdiction, limitation and attachments before use.
No statute, penalty, interest rate, compensation figure, or case citation has been invented or added.
Case reference: {state.case_id}; reviewed version: {state.version}.
"""


def save_draft(state: CaseState, kind: DocumentKind) -> dict:
    prior = next(
        (
            x
            for x in state.drafts
            if x["version"] == state.version and x["kind"] == kind
        ),
        None,
    )
    if prior:
        return prior
    text = render_document(state, kind)
    draft = {"id": uuid4().hex, "kind": kind, "version": state.version, "text": text}
    if state.draft_directory is not None:
        directory = Path(state.draft_directory) / state.case_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{draft['id']}.md"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
        draft["path"] = str(path)
        # This is a factual snapshot, not a synthesized transcript.
        (directory / "case.json").write_text(
            json.dumps(state.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    state.drafts.append(draft)
    return draft
