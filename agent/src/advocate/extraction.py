"""Model interprets each user turn once; validated application state owns effects."""

import json
from typing import Literal

from livekit.agents import llm
from pydantic import BaseModel, Field

from advocate.case import FactInput


class TurnInterpretation(BaseModel):
    requested_action: Literal[
        "continue", "practice", "end_practice", "draft", "advice", "summary"
    ] = "continue"
    updates: list[FactInput] = Field(default_factory=list)
    intent: Literal[
        "other", "confirm_draft", "decline_draft", "conditional_or_question"
    ] = "other"
    urgent_issue: str = ""
    urgent_quote: str = ""


EXTRACT = """You extract case state from a real user's latest message for an Indian consumer-refund assistant. Return JSON only matching the supplied schema. You do NOT give legal advice or respond to the user.
Record ALL facts volunteered together, not just the category. Never omit amount, merchant, item, dates, place, purpose, desired outcome, available evidence, merchant response or prior contact if supplied. No facts beyond the latest message; prior state helps resolve references only. Every quote must be an exact substring of that user message, in its original language. Translate/normalize the value carefully but never invent a fact. Classify category consumer_refund when appropriate, unsupported otherwise; quote the actual problem.
For amount, retain any supplied currency in the value, for example INR 8000. Never drop the currency or silently infer one when it was not supplied.
Use operation correct only for an explicit correction by this user, unknown when the user retracts certainty, otherwise record. Do not silently replace conflicting facts. Reuse the previous representation when the meaning is unchanged. For user statements about evidence, record only availability and limitations, not an assertion that evidence was authenticated. Never treat a quoted merchant statement or hypothetical as the user's admission. Omit facts from fictional rehearsal.
A bare conflicting amount such as a new 'I paid 8000' after previously saying 5000 must use record so both versions are preserved for clarification. It is not by itself an explicit correction. If they explain that they checked the receipt and correct the old amount, correct is appropriate.
intent confirm_draft ONLY if there is an existing delivered review and this latest real message unconditionally confirms it and wants the draft. A question, quote, correction mixed with approval, refusal, or condition is not confirmation. Use conditional_or_question or decline_draft as appropriate. Never mark confirm_draft on a request for a new draft before review.
urgent_issue/urgent_quote: identify immediate danger, violence, arrest, urgent legal deadline or serious consequences requiring professional help; supporting quote must be verbatim, else empty. Do not infer emergency merely from a refund complaint.
requested_action is what the user wants NEXT. Use practice when they ask to rehearse or role-play, draft when they ask for a document, advice when they ask what to do or their options, summary for a case summary, continue otherwise. An actual request to practise is sufficient; do not require an extra permission turn.
When case_data.mode is practice, return updates=[] regardless of what the fictional speaker says. Use end_practice when the user asks to stop, return to the real case, or receive final feedback. Urgency may still be detected for a real immediate risk, but not a merely fictional threat in rehearsal.
"""


async def interpret_turn(
    model, state, message, recent_context: str
) -> TurnInterpretation:
    ctx = llm.ChatContext()
    ctx.add_message(
        role="system",
        content=EXTRACT
        + "\nJSON SCHEMA:\n"
        + json.dumps(TurnInterpretation.model_json_schema()),
    )
    ctx.add_message(
        role="user",
        content=json.dumps(
            {
                "case_data": state.prompt_snapshot(),
                "recent_assistant_context": recent_context,
                "latest_actual_user_message": message.text_content,
            },
            ensure_ascii=False,
        ),
    )
    response = await model.chat(
        chat_ctx=ctx, response_format=TurnInterpretation
    ).collect()
    return TurnInterpretation.model_validate_json(response.text or "{}")
