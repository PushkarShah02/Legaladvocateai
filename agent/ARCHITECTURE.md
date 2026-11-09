# Consultation architecture

The application owns structured state and effects; the model interprets natural
language. There are no keyword, regex or phrase lists that classify user intent.
Substring matching validates supporting quotations, not their meaning.

## Runtime path

1. Existing LiveKit STT or typed chat supplies an actual user message.
2. `CaseAgent.llm_node` observes the message IDs for either input route. This
   avoids depending on a turn hook that typed `generate_reply` can bypass.
3. One structured LLM pass extracts fact patches, draft-confirmation meaning,
   urgency and requested action. It receives the latest message, compact case
   state and recent assistant context. Pydantic validates the output schema.
4. `CaseState.patch` validates every patch before mutation, checks verbatim
   user-source quotes and preserves omissions. Conflicting claims remain visible;
   explicit corrections have an audit trail. Uncertainty is a separate basis.
5. A compact state snapshot is injected into the normal voice LLM. It decides
   whether to ask, look up a source, explain options, summarize or request a draft
   review. Practice entry/exit decisions route explicit SDK tool handoffs once.
6. Tools enforce readiness, source integrity, versioned review and draft effects.
   They return structured facts/errors rather than fabricated successful outcomes.

Each session has its own `CaseState` in `AgentSession.userdata`. There is no
global current user or current case. Dates, opposing claims, evidence descriptions,
identifying details and source provenance live in structured fields. The audit
records previous values, conflicts and correction sources. A user-reported
invoice never becomes authenticated evidence.

## Modules

| Module | Responsibility |
|---|---|
| `src/agent.py` | Existing LiveKit entrypoint, audio providers, per-session wiring, text delivery |
| `advocate/extraction.py` | Model-based structured interpretation of each user turn |
| `advocate/case.py` | Case state, atomic fact patches, contradictions, version/review guards |
| `advocate/legal.py` | Bounded source verification and conditional options/readiness packet |
| `advocate/documents.py` | Deterministic preparation templates, placeholders, local draft commit |
| `advocate/workflow.py` | Consultation and practice agents, tools, handoffs and delivery receipts |
| `advocate/prompts.py` | Compact voice, consultation and rehearsal policies |

## Draft protocol

A case must have a merchant, purchase, problem, requested outcome and supported
category, with no unresolved contradictions or urgent-risk flag. Missing amounts,
dates or identifying details remain placeholders; a specific legal analysis uses
the stricter readiness checklist. `review_for_draft` generates a child review and
waits for successful, uninterrupted output. No review receipt is stored for failed
generation, interruption or a changed version. Its tool result requests no extra
automatic reply, avoiding duplicate confirmations.

`create_draft` requires a later real message that the structured interpreter
classified as unconditional confirmation, a matching review version, and continued
readiness. The model cannot bypass this by supplying a boolean approval argument.
Rendering uses the recorded facts and the original amount statement so a
normalization cannot silently drop the reported currency. Small local writes are
serialized on the session event loop; failed writes do not add a successful draft
receipt. Repeated calls for the same version/kind return the existing draft.

After a successful local commit, the application sends draft text over `lk.chat`.
Delivery failure is reported independently from local save success. Tests verify
actual local files; browser receipt has not been proven by the text-only tests.
No external notice-sending, filing, signature or legal representation is implemented.

## Practice isolation

Practice is an SDK handoff, not merely a prompt telling the model to pretend.
Mode is committed in `on_enter`, because an interrupted handoff may never take
effect. Practice has only an exit tool. It cannot modify facts or create documents.
Practice user-message IDs are excluded when consultation resumes. A model-based
exit decision forces the real exit tool; saying "practice ended" alone is not a
state transition. Explicit feedback output is completed before returning control.

## Performance and limits

The structured pass adds a model call per user turn. Tool follow-ups reuse its
result; compact snapshots avoid repeating long source quotations. The existing
model is shared across agents. Source lookup is local, hashed and bounded, so no
open-web search is on the normal voice path. The 12-second extraction timeout
fails visibly rather than inventing state. Speculative generation is off because
an unfinished user turn must not authorize a state mutation.

The LLM still controls natural-language wording and semantic extraction. Provenance
checks establish that a quote was actually spoken, not that the extracted meaning
is correct or the alleged event happened. Prompt-only constraints on free-form
legal speech are not a formal hallucination proof. Real-model regression tests,
source maintenance and human review remain necessary. Text tests do not establish
speech recognition accuracy, accent quality, cancellation under live interruption,
or legal correctness in a real dispute.
