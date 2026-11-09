# GitHub and Vercel deployment

The Python agent is deployed separately on LiveKit Cloud in `ap-south`.
Vercel runs only the Next.js frontend and its server-side token route. No local
Python worker, Python dependencies or Anam JavaScript SDK are needed by Vercel.

## Vercel settings

Import the GitHub repository and select **Next.js**, with **Root Directory** set
to **`frontend`**. Select **Node.js 24.x**. Keep the framework output directory
default. `frontend/vercel.json` pins installation to pnpm 9.15.9 with a frozen
lockfile, runs `npm run build`, and places server functions in Mumbai (`bom1`).
There is no static export: `/api/token` must execute on the server.

Set these variables in Vercel's **Production** environment; also set them in
**Preview** if preview deployments should connect to the agent:

| Name                 | Value                                                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `LIVEKIT_URL`        | The `wss://...livekit.cloud` URL for the deployed agent's project; copy from your ignored local env file or LiveKit project settings. |
| `LIVEKIT_API_KEY`    | API key for that same project. Server-side only.                                                                                      |
| `LIVEKIT_API_SECRET` | Matching API secret. Server-side only; mark Sensitive in Vercel.                                                                      |
| `AGENT_NAME`         | `my-agent`, matching the Python `rtc_session` registration.                                                                           |

`AGENT_NAME` is a dispatch name, not the `CA_...` deployment ID. The token route
always selects this name and the production deployment; browser-supplied agent,
room or deployment overrides are ignored. The hosted worker receives the job
from LiveKit Cloud. Stop local workers with the same dispatch name when testing
the hosted system so they do not also compete for jobs.

Do **not** add `NEXT_PUBLIC_LIVEKIT_API_KEY`, `NEXT_PUBLIC_LIVEKIT_API_SECRET`,
`ANAM_API_KEY`, `ANAM_AVATAR_ID`, model-provider keys, `LIVEKIT_TOKEN_SERVER_ID`,
or `IS_VERCEL_PREVIEW` to Vercel. Anam configuration stays in the Python agent's
LiveKit Cloud secrets. `NODE_ENV` is set by the platform. `FRONTEND_BUILD_DIR` is
only an optional local verification override and should remain unset in Vercel.

Public access without sign-in is intentional. Anyone who can access the site
can start a billable session. Cross-origin browser requests are rejected, but
this is not bot protection; use Vercel Firewall rate limits for `/api/token`
and LiveKit usage limits appropriate to your public launch.

## Local production verification

From `frontend`, with dependencies installed and ignored `.env.local` populated:

```powershell
npm run typecheck
npm run build
npm run start -- --port 3100
```

In another terminal, also from `frontend`:

```powershell
$env:FRONTEND_TEST_URL = 'http://127.0.0.1:3100'
node --env-file=.env.local scripts/check-local.mjs
node scripts/check-secrets.mjs
```

The endpoint check verifies JWT signature, expiry, unique rooms, forced agent
dispatch, cross-origin rejection and no raw credentials in responses. It mints
tokens but does not join rooms or start billable agent sessions. A browser call
is still needed to verify hosted microphone, avatar playback and transcript
download end to end.

## GitHub preparation

Commit application source, `frontend/pnpm-lock.yaml`, `frontend/vercel.json`,
empty `.env.example` files and the ignore rules. The root `.gitignore` excludes
real environment files, local tools, dependencies, builds, transcripts and case
artifacts across both folders. Never force-add these excluded files. The agent's
`livekit.toml` contains project/deployment identifiers, not API secrets.

No Git repository/history was present in this workspace during preparation, so
there was no prior commit history to audit. Before publishing, review the staged
file list (`git diff --cached --name-only`) and enable GitHub secret scanning.
The local secret checker compares publishable source/client bundles against
configured credentials without printing them. If secrets were previously pushed
elsewhere, rotate those keys; ignoring a file does not remove it from history.

Deployment and pushing remain separate actions requiring your approval.

Official references: [Vercel root directory](https://vercel.com/docs/monorepos),
[Vercel environment variables](https://vercel.com/docs/environment-variables),
[LiveKit authentication](https://docs.livekit.io/frontends/build/authentication/).
