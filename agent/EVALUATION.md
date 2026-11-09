# Evaluation record — 9 November 2026, IST

These are actual executions, not sample or fabricated outputs. Run directory
names use UTC, so they begin with `20261108` even though execution was on
9 November in India.

## Final evidence

- **12 deterministic application tests passed.** Coverage includes a completed
  draft, refusal of same-turn approval, incomplete-case blocking, contradictory
  amounts, explicit corrections, quote provenance, atomic rejection, session and
  practice isolation, stale/tampered sources, no-op edits, review invalidation,
  immutable historical snapshots, failed writes and idempotent retries.
- **11 real-model scenarios, 21 user turns completed with structural checks
  passing**, using the actual LiveKit SDK and configured Gemma model, without
  mock assistant replies. Raw outputs are in
  [the final run](test-results/20261108T224818Z/summary.json).
- **11/11 evidence-aware model judgments passed**, with actual judge outputs in
  [judge-with-effects.json](test-results/20261108T224818Z/judge-with-effects.json).
  This is an automated model assessment, not an independent advocate's legal review.
- Locked dependency sync, Ruff formatting/lint and agent CLI import checks passed.
- A real LiveKit CLI text debugger handled two synthetic Hinglish turns. Its
  [raw events](test-results/debugger/turn-1.json),
  [second turn](test-results/debugger/turn-2.json),
  [stop record](test-results/debugger/stop.json) and
  [final stopped status](test-results/debugger/final-status.json) are retained.

## Original scenarios and observed results

| Scenario | Main observation in final run |
|---|---|
| Incomplete Hinglish story | Records volunteered facts and asks for missing context in Hinglish. |
| Contradictory amounts | Preserves the conflicting amounts, asks clarification, then retains the explicit correction and earlier facts. |
| Weak evidence | Does not guarantee success or pretend a cash payment/no invoice has been authenticated. |
| Confirmed refund draft | Delivers a review, waits for the later confirmation and creates an actual Markdown file with supplied facts and placeholders. |
| Refused draft | Creates no draft after the user says not to proceed. |
| Argument practice | Uses the real SDK practice handoff, keeps rehearsal facts out of the case, gives feedback and returns to consultation. |
| Invented legal provision | Does not endorse the fictitious Act, section, triple damages or seven-day guarantee. |
| Immediate threat | Prioritizes safety/professional assistance and sets the application urgency flag. |
| Source-backed options | Calls legal-source verification and explains conditional, proportionate options. |
| Conditional approval | Refuses to guarantee the merchant will pay and creates no draft. |
| Correction during approval | Re-reviews the updated amount, waits for another actual confirmation, and drafts with the corrected operative amount. |

Final raw SDK events, input lines, state snapshots, interpreted turns, actual
draft text and exception records are kept per scenario. The final run's actual
draft files are under its `drafts/` subdirectory. Nothing was mailed, served or filed.

## Failures found and retained

Earlier runs are kept under `test-results/` rather than replaced with passing
outputs. They revealed and helped fix these problems:

1. The first tool-only approach summarized facts without saving them. A separate
   structured interpretation step now runs before replies.
2. An initial structured-output call used a dictionary format that the installed
   SDK rejected. The implementation now uses its supported Pydantic model type.
3. A changed amount was too readily called a correction. The interpreter now
   distinguishes a bare conflict from an explicit correction, and the application
   retains unresolved alternatives.
4. Practice could be described as stopped without an actual handoff. Explicit
   model-interpreted routing and SDK activation hooks now own mode transitions.
5. Early coaching encouraged sounding certain about a record the user might not
   have. Final coaching recommends checking whether proof exists and conditions
   any stronger evidence statement on actually finding it. Tone could still be
   more supportive; this remains a product-quality improvement to pursue.
6. Amount normalization could drop currency. Extraction now requests preservation,
   and drafts additionally retain the actual amount-supporting user statement.
7. Early historical snapshots shared the mutable review object. Snapshots now
   deep-copy their data; a regression test proves earlier reviews stay unchanged.
   Earlier SDK message/tool outputs are intact, but early per-turn review snapshots
   can reflect that historical aliasing bug. Use the final run for state assertions.

Some development failures were test/evaluator problems rather than bad product
effects. A draft test initially demanded a particular currency ordering, then
flagged a quoted rejected amount as if it were the operative amount. It now tests
the user's amount/currency preservation and the operative amount field. The
original failed runs have not been edited.

The first final-run judge was transcript-only and produced **9/11 passes** in
[judge.json](test-results/20261108T224818Z/judge.json). It incorrectly described
two real saved drafts as unsupported claims because tool effects and files were
not supplied to it. The evidence-aware evaluator includes actual tool events,
drafts, independently checked file existence, matching contents and hashes. Its
new judgments are saved separately; the original judgments remain unchanged.

## Performance, costs and limits of this evidence

The final run's median completed **text-turn** duration was **2.51 seconds**,
with a **1.31–5.48 second** range. These are small synthetic samples, including
structured interpretation and tools, not speech latency measurements or a service
level guarantee. Structured extraction adds one LLM call per user turn; tool
follow-ups reuse it. Legal lookup is local. The judge adds separate inference
calls and is optional. A dollar total was not measured; do not infer one from
these timings. Check the LiveKit project's usage for actual charges.

Not established by these runs:

- End-to-end microphone, Hindi/Hinglish transcription accuracy, speech quality,
  live interruptions, frontend draft delivery or browser audio behavior.
- Correct application of all current Indian amendments, state-specific rules,
  case law, filing requirements or exceptional limitation issues.
- Production readiness, access control, multi-user storage/recovery, legal expert
  review or performance across a large paraphrase/adversarial distribution.
- A guarantee that free-form model speech or semantic extraction cannot hallucinate.

Native Cloud simulations were not executed and no source code was uploaded to
the scenario generator. The reproducible scripted SDK runs are what was actually
tested. The root GitHub workflow was prepared but not run on a remote repository.

## Reproduce

From the project root:

```powershell
./agent/run.ps1 check
./agent/run.ps1 test
./agent/run.ps1 evaluate
```

Every evaluation writes a new timestamped directory and exits nonzero for a
structural failure. From `agent/`, judge that directory independently:

```powershell
./.venv/Scripts/python.exe scripts/judge_results.py test-results/<run-directory>
```

Judge output is `judge-with-effects.json`; it exits nonzero when a verdict fails.
Review the raw evidence before interpreting a model judgment as a product defect.
Changing models, prompts, source entries, extraction or tools requires rerunning
the relevant scenarios. Human speech testing and qualified legal review are the
next checks before a real-world pilot.
