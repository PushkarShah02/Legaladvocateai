import { existsSync, readFileSync, writeFileSync } from 'node:fs';

const keys = ['LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET'];
const values = new Map();
for (const path of ['../../agent/.env.local', '../../agent/.env']) {
  const source = new URL(path, import.meta.url);
  if (!existsSync(source)) continue;
  for (const line of readFileSync(source, 'utf8').split(/\r?\n/)) {
    const match = line.match(
      /^\s*(?:export\s+)?(LIVEKIT_URL|LIVEKIT_API_KEY|LIVEKIT_API_SECRET)\s*=\s*(.*)$/
    );
    if (
      match &&
      !values.has(match[1]) &&
      match[2].trim() &&
      !['""', "''"].includes(match[2].trim())
    )
      values.set(match[1], match[2]);
  }
}
const missing = keys.filter((key) => !values.has(key));
if (missing.length)
  throw new Error(
    `Missing agent credentials: ${missing.join(', ')}. Populate agent/.env.local or agent/.env.`
  );
const destination = new URL('../.env.local', import.meta.url);
const existing = existsSync(destination) ? readFileSync(destination, 'utf8') : '';
const retained = existing
  .split(/\r?\n/)
  .filter(
    (line) =>
      !/^\s*(?:export\s+)?(?:LIVEKIT_URL|LIVEKIT_API_KEY|LIVEKIT_API_SECRET|AGENT_NAME|LIVEKIT_TOKEN_SERVER_ID)\s*=/.test(
        line
      )
  );
writeFileSync(
  destination,
  [...retained, ...keys.map((key) => `${key}=${values.get(key)}`), 'AGENT_NAME=my-agent', ''].join(
    '\n'
  )
);
console.log('Synced LiveKit credentials to frontend/.env.local (values hidden). Agent: my-agent.');
