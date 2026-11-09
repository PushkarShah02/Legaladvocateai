# AI Advocate frontend

Next.js frontend based on LiveKit agent-starter-react. Existing branding, voice,
chat, Anam video, camera/screen sharing, themes and transcript downloads remain.

## Run against the Cloud agent

From `frontend/`, populate ignored `.env.local` from `.env.example`, using the
same LiveKit Cloud project as the deployed Python agent. Set `AGENT_NAME=my-agent`.

```powershell
npm exec --yes --package=pnpm@9.15.9 -- pnpm install --frozen-lockfile
npm run dev
```

Open http://localhost:3000. No local Python worker is required. Stop local workers
with the same dispatch name when testing the hosted agent. The server token route
creates a fresh room and dispatches only the configured production agent. Anam
video/audio arrives through LiveKit; no Anam keys belong in this frontend.

`npm run env:sync` copies credentials from the sibling agent folder for local use
only. It is not invoked by install, build or runtime. Vercel needs no agent files.

## Vercel setup

See [the full deployment guide](../DEPLOYMENT.md). Use Root Directory `frontend`,
framework Next.js and Node.js 24.x. `vercel.json` pins pnpm 9.15.9 installation
with `pnpm-lock.yaml` and selects Mumbai for server functions.

Required server variables: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.
Also set `AGENT_NAME=my-agent` explicitly (the default). No `NEXT_PUBLIC_` secrets,
Anam/model keys, development token server or preview bypass variables are needed.
Public access without sign-in is intentional; configure public-use rate limits
and billing limits before sharing broadly.

## Checks

```powershell
npm run typecheck
npm run lint
npm run build
npm run start -- --port 3100
```

In another terminal:

```powershell
$env:FRONTEND_TEST_URL = 'http://127.0.0.1:3100'
node --env-file=.env.local scripts/check-local.mjs
node scripts/check-secrets.mjs
```

Token checks do not join rooms or start agent sessions. Browser testing is still
needed for microphone permissions, avatar playback and transcript downloads.
Camera and screen sharing remain available; the agent does not interpret video.

Transcripts download as timestamped `.txt` files on disconnect; a manual button
provides a fallback. Exports include voice transcriptions and chat received by
this page. Browser downloads can be blocked; closing or refreshing the page can
lose its in-memory transcript.

Upstream MIT license retained in `LICENSE`. Upstream `.github` files in this
subdirectory are reference material, not repository-root workflows.
