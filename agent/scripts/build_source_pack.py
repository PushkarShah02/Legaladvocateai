"""Rebuild a reviewed source pack from the downloaded official Gazette PDF.

This deliberately does not invent an online retrieval success. Keep the reviewed
source files, URLs, hashes and original review timestamp together.
"""

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1] / "references" / "legal"


def build():
    statute = ROOT / "consumer-protection-act-2019.pdf"
    text = "\n".join(page.extract_text() for page in PdfReader(statute).pages)

    def excerpt(start, end):
        return text[text.index(start) : text.index(end, text.index(start))].strip()

    topics = {
        "consumer_eligibility": {
            "source_id": "cpa2019",
            "provision": "Consumer Protection Act 2019, section 2(7)",
            "summary": "Paid goods/services can fall within consumer protection. Resale and commercial purpose are generally excluded, subject to the goods/self-employment livelihood explanation. Online purchases are included. Eligibility is fact-dependent.",
            "excerpt": excerpt('(7) "consumer" means', '(8) "consumer dispute"'),
        },
        "refund_remedies": {
            "source_id": "cpa2019",
            "provision": "Consumer Protection Act 2019, section 39(1)(a)-(d)",
            "summary": "If the relevant allegations are proved, commission orders can include removal of defects, replacement, return of price/charges with interest as decided, or compensation. A refund is not automatic for every disliked purchase.",
            "excerpt": excerpt("39. (1)", "(e) to pay"),
        },
        "limitation": {
            "source_id": "cpa2019",
            "provision": "Consumer Protection Act 2019, section 69",
            "summary": "The general admission rule is two years from when the cause of action arises; delay can be condoned for sufficient cause with recorded reasons. Accrual, exceptions and facts need review. Do not equate purchase date with accrual or calculate a definitive deadline.",
            "excerpt": excerpt("69. (1)", "70. (1)"),
        },
        "consumer_complaint": {
            "source_id": "cpa2019",
            "provision": "Consumer Protection Act 2019, section 35",
            "summary": "The consumer can file a complaint, including electronically in the prescribed manner. This alone does not establish the right forum, amount limits, fee, or current filing procedure.",
            "excerpt": excerpt("35. (1)", "36. (1)"),
        },
    }
    sources = {
        "cpa2019": {
            "title": "Gazette of India: Consumer Protection Act, 2019 (Act 35 of 2019)",
            "url": "https://egazette.gov.in/WriteReadData/2019/210422.pdf",
            "file": statute.name,
            "sha256": hashlib.sha256(statute.read_bytes()).hexdigest(),
            "checked_at": "2026-11-09T00:00:00+00:00",
            "scope": "Original enacted text, not a consolidated assurance of current law. Section 34(1) original monetary threshold is intentionally excluded.",
        }
    }
    # NCH snapshot is obtained separately from the official source, not generated.
    nch = ROOT / "nch.html"
    if nch.exists():
        content = nch.read_text(encoding="utf-8")
        if "1915" not in content or "pre-litigation" not in content:
            raise ValueError("The official NCH snapshot does not support this entry.")
        sources["nch"] = {
            "title": "Department of Consumer Affairs — National Consumer Helpline",
            "url": "https://consumerhelpline.gov.in/public/convergenceprogram",
            "file": nch.name,
            "sha256": hashlib.sha256(nch.read_bytes()).hexdigest(),
            "checked_at": "2026-11-09T00:00:00+00:00",
        }
        topics["nch"] = {
            "source_id": "nch",
            "provision": "Official administrative grievance channel",
            "summary": "National Consumer Helpline offers pre-litigation grievance redressal, including through consumerhelpline.gov.in and toll-free 1915. This is not adjudication and does not guarantee settlement or extend a filing limitation period.",
            "excerpt": "NCH has emerged as a single point of access for consumers across the country at the pre-litigation stage.",
        }
    (ROOT / "sources.json").write_text(
        json.dumps(
            {"sources": sources, "topics": topics}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(
        f"Built {len(topics)} reviewed legal topics; no other legal proposition is verified."
    )


if __name__ == "__main__":
    build()
