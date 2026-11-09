import { jwtVerify } from 'jose';
import assert from 'node:assert/strict';

const origin = process.env.FRONTEND_TEST_URL || 'http://127.0.0.1:3000';
const page = await fetch(origin);
assert.equal(page.status, 200, 'The home page should load');
const html = await page.text();
assert.ok(html.includes('AI Advocate'), 'The page should show project branding');
assert.ok(html.includes('Start a conversation'), 'The page should offer session start');
const response = await fetch(`${origin}/api/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    room_config: { agents: [{ agent_name: 'untrusted-agent', deployment: 'staging' }] },
  }),
});
assert.equal(response.status, 200, 'The local token endpoint should succeed');
assert.equal(response.headers.get('cache-control'), 'no-store');
const details = await response.json();
assert.equal(details.serverUrl, process.env.LIVEKIT_URL);
const { payload } = await jwtVerify(
  details.participantToken,
  new TextEncoder().encode(process.env.LIVEKIT_API_SECRET)
);
assert.equal(payload.iss, process.env.LIVEKIT_API_KEY);
assert.equal(payload.video.room, details.roomName);
assert.equal(payload.video.roomJoin, true);
assert.ok(
  JSON.stringify(payload.roomConfig).includes(process.env.AGENT_NAME || 'my-agent'),
  'Token must dispatch to the project agent'
);
const remainingSeconds = payload.exp - Math.floor(Date.now() / 1000);
assert.ok(!JSON.stringify(payload.roomConfig).includes('untrusted-agent'));
assert.ok(!JSON.stringify(payload.roomConfig).includes('staging'));
const second = await fetch(`${origin}/api/token`, { method: 'POST' }).then((res) => res.json());
assert.notEqual(second.roomName, details.roomName, 'Every call must get a unique room');
const crossSite = await fetch(`${origin}/api/token`, {
  method: 'POST',
  headers: { Origin: 'https://untrusted.example' },
});
assert.equal(crossSite.status, 403, 'Cross-origin token requests must be rejected');
assert.ok(remainingSeconds > 0 && remainingSeconds <= 900, 'Participant token must be short-lived');
for (const key of ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET']) {
  assert.ok(!html.includes(process.env[key]), `${key} must not appear in rendered HTML`);
  assert.ok(
    !JSON.stringify(details).includes(process.env[key]),
    `${key} must not appear in token response`
  );
}
console.log(
  'PASS: branded page, signed participant token, my-agent dispatch, expiry, no-store, and no raw API credentials in responses. No agent started.'
);
