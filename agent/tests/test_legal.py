import json
from datetime import datetime, timezone

from advocate.case import CaseState
from advocate.legal import PACK, LegalLibrary, analysis_packet


def test_supported_law_has_official_source_and_no_invented_rule():
    result = LegalLibrary().lookup(
        "refund_remedies", now=datetime(2026, 11, 9, tzinfo=timezone.utc)
    )
    assert result["status"] == "verified_source_snapshot"
    assert result["url"].startswith("https://egazette.gov.in/")
    assert "39" in result["provision"]
    assert "return to the complainant" in result["excerpt"]
    assert (
        LegalLibrary().lookup("section 420 refund within 7 days")["status"]
        == "unverified"
    )


def test_old_sources_are_not_presented_as_currently_verified():
    result = LegalLibrary().lookup(
        "limitation", now=datetime(2030, 1, 1, tzinfo=timezone.utc)
    )
    assert result["status"] == "reference_only"
    assert "summary" not in result


def test_source_tampering_fails_closed(tmp_path):
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    (tmp_path / "sources.json").write_text(json.dumps(pack), encoding="utf-8")
    for source in pack["sources"].values():
        (tmp_path / source["file"]).write_bytes(b"not the verified source")
    assert (
        LegalLibrary(tmp_path / "sources.json").lookup("refund_remedies")["status"]
        == "unverified"
    )


def test_no_analysis_for_missing_facts_or_unverified_law():
    assert analysis_packet(CaseState())["status"] == "needs_information"
