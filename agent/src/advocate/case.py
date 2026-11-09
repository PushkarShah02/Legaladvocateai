"""Versioned, per-session state. The model interprets meaning; code validates effects."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

FactField = Literal[
    "category",
    "merchant",
    "purchase",
    "amount",
    "purchase_date",
    "problem_date",
    "problem",
    "location",
    "purpose",
    "desired_outcome",
    "merchant_response",
    "contact_attempt",
    "evidence",
    "consumer_name",
    "consumer_address",
    "merchant_address",
    "order_id",
    "language",
    "reply_by",
]
DocumentKind = Literal["refund_request", "consumer_complaint"]
REQUIRED = (
    "merchant",
    "purchase",
    "amount",
    "purchase_date",
    "problem_date",
    "problem",
    "location",
    "purpose",
    "desired_outcome",
    "merchant_response",
)


class FactInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: FactField
    value: str = Field(min_length=1, max_length=1500)
    quote: str = Field(
        min_length=1,
        max_length=3000,
        description="Exact supporting text from a real user message, never from the assistant or a hypothetical.",
    )
    operation: Literal["record", "correct", "unknown"] = "record"


@dataclass
class Fact:
    value: str
    quote: str
    message_id: str
    basis: str = "user_report"


@dataclass
class CaseState:
    case_id: str = field(default_factory=lambda: uuid4().hex)
    version: int = 0
    facts: dict[str, Fact] = field(default_factory=dict)
    conflicts: dict[str, dict] = field(default_factory=dict)
    messages: dict[str, str] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)
    mode: str = "consultation"
    risk: str = "none"
    risk_reason: str = ""
    legal_receipts: dict[str, dict] = field(default_factory=dict)
    review: dict | None = None
    drafts: list[dict] = field(default_factory=list)
    interpreted: dict[str, dict] = field(default_factory=dict)
    extraction_error: str = ""
    routed_practice: set[str] = field(default_factory=set)
    routed_practice_end: set[str] = field(default_factory=set)
    # Runtime-only adapters, deliberately excluded from snapshots.
    publish_text: object = field(default=None, repr=False)
    draft_directory: object = field(default=None, repr=False)

    def observe(self, message_id: str, text: str) -> None:
        if message_id not in self.messages:
            self.messages[message_id] = text

    def source(self, quote: str, *, latest: bool = False) -> str:
        items = list(self.messages.items())
        if latest:
            items = items[-1:]
        for message_id, text in reversed(items):
            if quote.strip() and quote in text:
                return message_id
        raise ValueError("Supporting quote must occur verbatim in a real user message.")

    def patch(self, updates: list[FactInput]) -> dict:
        if self.mode != "consultation":
            raise ValueError("Real-case changes are blocked during practice.")
        if len(updates) > 20 or len({x.field for x in updates}) != len(updates):
            raise ValueError("Use at most 20 distinct fields per patch.")
        proposed, conflicts, events = deepcopy(self.facts), deepcopy(self.conflicts), []
        for update in updates:
            message_id = self.source(
                update.quote, latest=update.operation in ("correct", "unknown")
            )
            value = update.value.strip()
            fact = Fact(
                value=value,
                quote=update.quote,
                message_id=message_id,
                basis="unknown" if update.operation == "unknown" else "user_report",
            )
            prior = proposed.get(update.field)
            if (
                prior
                and prior.value == value
                and prior.basis == fact.basis
                and update.field not in conflicts
            ):
                continue
            if prior and update.operation == "record" and prior.value != value:
                conflicts[update.field] = {
                    "previous": asdict(prior),
                    "new": asdict(fact),
                }
                events.append(
                    {
                        "field": update.field,
                        "operation": "conflict",
                        "source": message_id,
                    }
                )
            else:
                proposed[update.field] = fact
                conflicts.pop(update.field, None)
                events.append(
                    {
                        "field": update.field,
                        "operation": update.operation,
                        "source": message_id,
                        "previous": asdict(prior) if prior else None,
                    }
                )
        if events:
            self.facts, self.conflicts = proposed, conflicts
            self.version += 1
            self.review = None
            self.audit.extend({**event, "version": self.version} for event in events)
        return self.snapshot()

    def value(self, name: str, placeholder: str = "[Not supplied]") -> str:
        fact = self.facts.get(name)
        return fact.value if fact and fact.basis != "unknown" else placeholder

    def readiness(self) -> dict:
        missing = [
            name
            for name in REQUIRED
            if name not in self.facts or self.facts[name].basis == "unknown"
        ]
        category_supported = self.value("category", "") == "consumer_refund"
        return {
            "ready": not missing
            and not self.conflicts
            and self.risk == "none"
            and category_supported,
            "missing": missing,
            "contradictions": list(self.conflicts),
            "category_supported": category_supported,
            "risk": self.risk,
        }

    def mark_review(self, kind: DocumentKind) -> dict:
        if not self.draft_readiness()["ready"]:
            raise ValueError(
                "Case is incomplete, conflicted, urgent, or outside the supported category."
            )
        self.review = {
            "version": self.version,
            "after_message": next(reversed(self.messages)),
            "kind": kind,
            "approved": False,
        }
        return self.review

    def approve_review(self) -> None:
        if not self.review or self.review["version"] != self.version:
            raise ValueError("A delivered review of the current case is required.")
        if next(reversed(self.messages)) == self.review["after_message"]:
            raise ValueError(
                "Approval must be a later real user message after the review."
            )
        if not self.draft_readiness()["ready"]:
            raise ValueError("Case no longer ready for drafting.")
        self.review["approved"] = True
        self.review["approval_message"] = next(reversed(self.messages))

    def draft_readiness(self) -> dict:
        essential = ("merchant", "purchase", "problem", "desired_outcome")
        missing = [
            name
            for name in essential
            if name not in self.facts or self.facts[name].basis == "unknown"
        ]
        return {
            "ready": not missing
            and not self.conflicts
            and self.risk == "none"
            and self.value("category", "") == "consumer_refund",
            "missing": missing,
            "placeholders_required": self.readiness()["missing"],
            "contradictions": list(self.conflicts),
            "risk": self.risk,
        }

    def snapshot(self) -> dict:
        return deepcopy(
            {
                "case_id": self.case_id,
                "version": self.version,
                "mode": self.mode,
                "facts": {k: asdict(v) for k, v in self.facts.items()},
                "timeline": {
                    k: asdict(v)
                    for k, v in self.facts.items()
                    if k in ("purchase_date", "problem_date", "contact_attempt")
                },
                "contradictions": self.conflicts,
                "readiness": self.readiness(),
                "draft_readiness": self.draft_readiness(),
                "risk_reason": self.risk_reason,
                "review": self.review,
                "legal_topics_checked": list(self.legal_receipts),
                "drafts": [
                    {"id": x["id"], "kind": x["kind"], "path": x.get("path")}
                    for x in self.drafts
                ],
            }
        )

    def prompt_snapshot(self) -> dict:
        data = self.snapshot()
        data.pop("timeline")
        data["facts"] = {
            key: {
                "value": fact.value,
                "basis": fact.basis,
                "source_message": fact.message_id,
            }
            for key, fact in self.facts.items()
        }
        data["contradictions"] = {
            key: {"previous": value["previous"]["value"], "new": value["new"]["value"]}
            for key, value in self.conflicts.items()
        }
        return data
