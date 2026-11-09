# AI Advocate

- `agent/`: Python voice agent, deployed separately on LiveKit Cloud.
- `frontend/`: Next.js voice/avatar frontend and server-side LiveKit token API.

For GitHub and Vercel setup, see [DEPLOYMENT.md](DEPLOYMENT.md). Use `frontend`
as the Vercel root directory. Real credentials, case artifacts, local test results
and generated files are excluded by the root and per-project ignore rules.

The frontend connects to the hosted agent; running Python locally is optional.
Deployment and pushing code require explicit approval.
