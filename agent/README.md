# AI Advocate — consumer-refund MVP

An Indian legal-information assistant built on the existing LiveKit Python
agent. It is an AI assistant, not a licensed advocate. The supported deep
workflow is a consumer refund dispute; criminal defence, landlord deposits,
employment disputes and other categories are not implemented as specialist flows.

## Run

Dependencies, local Python 3.12 and model files are installed. From the root:

```powershell
./agent/run.ps1 dev
```

In another terminal:

```powershell
cd frontend
npm run dev
```

Open http://localhost:3000. Try describing a refund problem naturally, ask for
options, request a refund letter, or ask to practise responding to the merchant.
Use the chat toggle for the transcript and delivered draft text. Drafts are also
saved under `agent/artifacts/<case-id>/`. No notice is sent and no complaint is filed.

For microphone/speaker testing directly in your terminal:

```powershell
./agent/run.ps1 console
```

The agent still registers as `my-agent`, matching the frontend configuration.

## Anam talking avatar

Anam is integrated with the existing Python session through
`livekit-plugins-anam==1.8.10`. Set `ANAM_API_KEY` and `ANAM_AVATAR_ID` in
`agent/.env.local`; neither belongs in frontend configuration. Restart the agent
after saving. The avatar starts before the voice session and uses the existing
Fish Audio speech. The existing frontend renders the avatar video automatically.

Optional settings: `ANAM_ENABLED=false` for voice-only mode,
`ANAM_AVATAR_NAME=AI Advocate`, and `ANAM_AVATAR_MODEL=cara-4.1-express`.
Terminal console sessions without a connected room remain voice-only.
Missing credentials or avatar startup failure also retain voice-only mode;
check the agent logs if no face appears. Startup waits for the avatar video track,
and the SDK removes the avatar participant on job shutdown. Anam account usage
applies to live avatar sessions. No separate Anam voice or LLM is configured.

To verify key/ID access without starting a video session, from `agent/` run:

```powershell
./.venv/Scripts/python.exe scripts/check_anam.py
```

This read-only check does not establish lip sync, browser playback or interruption
behavior. Test those by starting both terminals and opening the frontend.
Integration references: [LiveKit Python guide](https://docs.livekit.io/agents/models/avatar/plugins/anam/)
and [Anam LiveKit integration](https://anam.ai/integrations/livekit).

## What changed

- A structured model pass extracts volunteered facts before each response. The
  per-session case holds claims, source quotes, dates, people, evidence reports,
  missing information, contradictions, revisions and the requested outcome.
- Case-specific analysis is gated on sufficient facts, unresolved contradictions,
  urgent risk, and source verification. The assistant chooses its next question
  naturally rather than running a fixed questionnaire.
- A small primary-source library covers consumer eligibility, possible refund
  remedies, limitation, complaint preparation and the National Consumer Helpline.
  Each entry includes its URL, provision, actual excerpt, retrieval/review date
  and source hash. Unknown propositions are explicitly unverified.
- Drafting has a delivered review, a later actual user confirmation and a version
  check. Corrections invalidate the review. Draft templates use recorded facts
  and placeholders. A refusal or conditional approval cannot create a draft.
- Argument practice uses a separate LiveKit agent with no case-editing or
  drafting tools. Model-interpreted requests route actual SDK handoffs; fictional
  practice statements are excluded from real-case facts.
- Urgent risks block ordinary drafting and trigger professional/emergency
  orientation rather than pretending to provide criminal or emergency services.

The STT, main LLM, TTS, noise cancellation and LiveKit connection remain the
starter's providers. STT and TTS request English, and all conversational output
is English-only. Preemptive generation is disabled to avoid speculative case mutations.

## Credentials and installation

`agent/.env.local` already contains the LiveKit Cloud credentials. No separate
OpenAI, speech-provider, search or legal-database key is required.

Optional environment settings (defaults shown):

```dotenv
ADVOCATE_LLM_MODEL=google/gemma-4-31b-it
ADVOCATE_STT_MODEL=assemblyai/universal-3-6-pro
ADVOCATE_TTS_MODEL=fishaudio/s2.1-pro
ADVOCATE_TTS_VOICE=fa4c9eb3dccc4806b382b40d61c6b10a
```

The replacement LLM must support function tools and Pydantic/JSON-schema
structured outputs through LiveKit Inference. Changing it requires rerunning the
conversation tests; provider compatibility is not assumed.

On another Windows checkout, install uv, then run `./agent/run.ps1 setup`.
The wrapper also supports the workspace-local `agent/.tools/uv.exe`. Managed
Python and package caches stay within `agent/`. Commit `uv.lock` for reproducibility.

## Tests and raw outputs

```powershell
./agent/run.ps1 check       # formatting, lint, imports
./agent/run.ps1 test        # deterministic application tests; no inference
./agent/run.ps1 evaluate    # original synthetic consultations; real inference
```

Real-model runs use the existing Cloud account and incur inference usage. Every
run writes a new directory in `agent/test-results/`; failures are retained.
`completed_ungraded` means the conversation completed and its structural checks
passed, not that the conversation has been judged legally correct.

From `agent/`, run a selected test or a separate real-model judge:

```powershell
./.venv/Scripts/python.exe scripts/evaluate.py --scenario confirmed_draft
./.venv/Scripts/python.exe scripts/judge_results.py test-results/<run-directory>
```

See [EVALUATION.md](EVALUATION.md) for the observed results and their limits.
`tests/consultations.json` contains the original scripted users and expectations.
`scenarios.yaml` mirrors them for LiveKit's native simulation tooling. Source code
was not uploaded to a scenario generator. The root GitHub workflow runs local
checks and, on main/manual runs with repository LiveKit secrets, the synthetic
conversation suite. It has not been executed on GitHub from this workspace.

## Boundaries and maintenance

See [ARCHITECTURE.md](ARCHITECTURE.md) and
[references/legal/README.md](references/legal/README.md).

This is a bounded prototype, not an exhaustive or continuously updated Indian
legal research system. It does not inspect uploaded documents, search case law,
calculate definitive filing deadlines, promise legal outcomes, authenticate users,
or submit proceedings. Complaint output is preparation material with forum and
procedure placeholders, not a filing-ready pleading.

Source snapshots expire after 30 days and fail closed for specific legal claims.
From `agent/`, `./.venv/Scripts/python.exe scripts/refresh_sources.py` re-fetches
the allowlisted official sources. Identical bytes can renew the source-check
timestamp; changed bytes are saved for manual review and never silently trusted.
This is a source-integrity check, not a guarantee of amendment completeness.

Case state lasts for the session; there is no cross-session case recovery.
Requested drafts and their case snapshots contain personal information and are
stored locally in ignored `artifacts/`; delete them when no longer needed.
Normal application case state is not automatically written to disk, but LiveKit
observability and console logs have their own retention settings. The committed
test outputs use fictional cases only.

### English voice delivery

All conversation is in English. The agent introduces itself as an AI lawyer and
asks for the user's name before asking how it can help. If the user already
shares their problem, intake proceeds without repeating it. The opening has no
licensing disclaimer. The existing male Fish voice and all providers are retained;
custom accent steering is removed. STT and TTS both request English.

Restart the agent and start a new conversation after changing prompts or settings.
From `agent/`, `./.venv/Scripts/python.exe scripts/preview_voice.py` generates an
English listening preview under `test-results/voice-language/english.wav` using
normal LiveKit Inference TTS usage, without starting Anam.

The original LiveKit starter's MIT license is retained in `LICENSE`.
