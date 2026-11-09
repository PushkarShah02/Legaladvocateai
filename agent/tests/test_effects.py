import pytest

from advocate.case import CaseState, FactInput
from advocate.documents import save_draft


def prepared_state():
    state = CaseState()
    state.observe("u1", "Acme sold me a broken phone. I want a refund.")
    state.patch(
        [
            FactInput(
                field=key,
                value=value,
                quote="Acme sold me a broken phone. I want a refund.",
            )
            for key, value in {
                "merchant": "Acme",
                "purchase": "phone",
                "problem": "broken phone",
                "desired_outcome": "refund",
                "category": "consumer_refund",
            }.items()
        ]
    )
    state.mark_review("refund_request")
    state.observe("u2", "Correct, please draft it.")
    state.approve_review()
    return state


def test_correction_invalidates_review_but_identical_fact_does_not():
    state = prepared_state()
    version = state.version
    state.patch([FactInput(field="merchant", value="Acme", quote="Acme sold me")])
    assert state.version == version and state.review["approved"]
    state.observe("u3", "Actually the shop is Zenith, not Acme.")
    state.patch(
        [
            FactInput(
                field="merchant",
                value="Zenith",
                quote="the shop is Zenith",
                operation="correct",
            )
        ]
    )
    assert state.review is None
    with pytest.raises(ValueError, match="review"):
        save_draft(state, "refund_request")


def test_failed_write_does_not_publish_success_and_retry_is_idempotent(tmp_path):
    state = prepared_state()
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("blocked")
    state.draft_directory = blocked
    with pytest.raises(OSError):
        save_draft(state, "refund_request")
    assert not state.drafts
    state.draft_directory = tmp_path / "drafts"
    first = save_draft(state, "refund_request")
    second = save_draft(state, "refund_request")
    assert first["id"] == second["id"]
    assert len(state.drafts) == 1
    assert "[Not supplied]" in first["text"]


def test_historical_snapshot_does_not_change_when_review_is_approved():
    state = prepared_state()
    state.mark_review("refund_request")
    before = state.snapshot()
    state.observe("u3", "These details are correct; please draft it.")
    state.approve_review()
    assert state.review["approved"]
    assert before["review"]["approved"] is False
