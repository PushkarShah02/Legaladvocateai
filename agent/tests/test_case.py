import pytest

from advocate.case import CaseState, FactInput
from advocate.documents import render_document


def test_refund_draft_requires_later_approval_and_uses_actual_facts():
    state = CaseState()
    state.observe(
        "u1",
        "I paid INR 8000 to Acme for a broken mixer on 2026-10-01 in Delhi for my home. I want a refund. They refused. It broke on 2026-10-02.",
    )
    values = {
        "category": "consumer_refund",
        "merchant": "Acme",
        "amount": "INR 8000",
        "purchase": "mixer",
        "purchase_date": "2026-10-01",
        "problem": "broken mixer",
        "problem_date": "2026-10-02",
        "location": "Delhi",
        "purpose": "my home",
        "desired_outcome": "refund",
        "merchant_response": "refused",
    }
    state.patch(
        [
            FactInput(
                field=k,
                value=v,
                quote="I paid INR 8000 to Acme for a broken mixer on 2026-10-01 in Delhi for my home. I want a refund. They refused. It broke on 2026-10-02.",
            )
            for k, v in values.items()
        ]
    )
    assert state.readiness()["ready"]
    state.mark_review("refund_request")
    with pytest.raises(ValueError, match="later"):
        state.approve_review()
    state.observe("u2", "That is correct, please draft it.")
    state.approve_review()
    draft = render_document(state, "refund_request")
    assert "INR 8000" in draft and "Acme" in draft and "2026-10-01" in draft
    assert "[Your name]" in draft and "[Merchant address]" in draft
    assert "guarantee" not in draft.lower()


def test_incomplete_case_cannot_be_reviewed_for_drafting():
    state = CaseState()
    state.observe("u1", "My headphones broke.")
    state.patch(
        [
            FactInput(
                field="problem", value="headphones broke", quote="My headphones broke."
            )
        ]
    )
    assert not state.readiness()["ready"]
    with pytest.raises(ValueError, match="incomplete"):
        state.mark_review("refund_request")


def test_contradiction_preserves_prior_fact_until_correction():
    state = CaseState()
    state.observe("u1", "I paid 5000.")
    state.patch([FactInput(field="amount", value="5000", quote="I paid 5000.")])
    state.observe("u2", "It was 8000.")
    state.patch([FactInput(field="amount", value="8000", quote="It was 8000.")])
    assert state.facts["amount"].value == "5000"
    assert "amount" in state.conflicts
    assert not state.readiness()["ready"]
    state.observe("u3", "I checked the receipt; 8000 is correct.")
    state.patch(
        [
            FactInput(
                field="amount",
                value="8000",
                quote="8000 is correct.",
                operation="correct",
            )
        ]
    )
    assert state.facts["amount"].value == "8000"
    assert not state.conflicts


def test_no_evidence_is_not_verified_evidence_and_fake_quote_rejected_atomically():
    state = CaseState()
    state.observe("u1", "No invoice. I paid cash.")
    state.patch(
        [
            FactInput(
                field="evidence",
                value="No invoice; cash payment",
                quote="No invoice. I paid cash.",
            )
        ]
    )
    assert state.facts["evidence"].basis == "user_report"
    version = state.version
    with pytest.raises(ValueError, match="quote"):
        state.patch([FactInput(field="merchant", value="Acme", quote="Acme sold it")])
    assert state.version == version and "merchant" not in state.facts


def test_session_isolation_and_practice_cannot_patch_real_case():
    first, second = CaseState(), CaseState()
    first.observe("u1", "My merchant is Acme.")
    first.mode = "practice"
    with pytest.raises(ValueError, match="practice"):
        first.patch(
            [FactInput(field="merchant", value="Acme", quote="My merchant is Acme.")]
        )
    assert not second.messages and not second.facts
