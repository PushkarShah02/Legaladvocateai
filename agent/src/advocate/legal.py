"""A bounded, auditable primary-source library, not open-web legal RAG."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "references" / "legal" / "sources.json"


class LegalLibrary:
    def __init__(self, path: Path = PACK):
        self.path = path

    def lookup(self, topic: str, *, now: datetime | None = None) -> dict:
        try:
            pack = json.loads(self.path.read_text(encoding="utf-8"))
            item = pack["topics"].get(topic)
            if item is None:
                return {
                    "status": "unverified",
                    "topic": topic,
                    "reason": "No reviewed primary-source entry for that proposition. Do not invent a section, judgment, deadline or penalty.",
                    "supported_topics": list(pack["topics"]),
                }
            source = pack["sources"][item["source_id"]]
            raw = (self.path.parent / source["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                return {
                    "status": "unverified",
                    "reason": "Source integrity check failed.",
                }
            checked = datetime.fromisoformat(source["checked_at"])
            age = ((now or datetime.now(timezone.utc)) - checked).total_seconds()
            if age < -86400 or age > 30 * 86400:
                return {
                    "status": "reference_only",
                    "reason": "Source review is older than 30 days or clock is inconsistent. Refresh and review before stating a specific legal rule.",
                    "url": source["url"],
                    "checked_at": source["checked_at"],
                }
            return {
                "status": "verified_source_snapshot",
                "topic": topic,
                **item,
                "title": source["title"],
                "url": source["url"],
                "checked_at": source["checked_at"],
                "sha256": source["sha256"],
                "limits": "Verified against the cited official source snapshot, not a guarantee of subsequent amendments, current portal availability, or applicability to this person. No case law search performed.",
            }
        except (OSError, ValueError, KeyError):
            return {
                "status": "unverified",
                "reason": "Legal source pack unavailable or malformed. Continue fact gathering; do not supply specific legal claims.",
            }


def analysis_packet(state) -> dict:
    if state.extraction_error:
        return {"status": "needs_information", "reason": state.extraction_error}
    gate = state.readiness()
    if not gate["ready"]:
        return {
            "status": "needs_information",
            **gate,
            "next": "Ask the most consequential missing or contradictory fact, one question at a time. General evidence-preservation suggestions are allowed.",
        }
    citations = [
        receipt
        for receipt in state.legal_receipts.values()
        if receipt["status"] == "verified_source_snapshot"
    ]
    if not citations:
        return {
            "status": "needs_verification",
            "next": "Look up an applicable legal topic before stating a specific legal rule.",
        }
    return {
        "status": "conditional_analysis",
        "facts": state.snapshot()["facts"],
        "evidence_status": "All case facts and document availability are user reports. No document has been inspected or authenticated.",
        "sources": citations,
        "options": [
            {
                "option": "Written merchant grievance",
                "benefit": "Creates a clear record and can resolve the issue without proceedings.",
                "risk": "Merchant may dispute the account or offer a repair; preserve the response.",
            },
            {
                "option": "National Consumer Helpline",
                "benefit": "Pre-litigation grievance channel, if the verified NCH source applies.",
                "risk": "Not a court order; settlement is not assured. Check the NCH source first.",
            },
            {
                "option": "Consumer commission preparation",
                "benefit": "May provide adjudication and relief if eligibility, merits and procedure are satisfied.",
                "risk": "Requires evidence, jurisdiction and limitation review; consumes time and may involve costs. No guaranteed refund.",
            },
        ],
        "next": "Explain the issue, reported strengths, evidentiary weaknesses and a proportionate next step. Distinguish legal source, user claim and inference. Do not calculate a final filing deadline.",
    }
