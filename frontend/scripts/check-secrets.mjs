import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const frontend = fileURLToPath(new URL('..', import.meta.url));
const root = resolve(frontend, '..');
const values = new Set();
// Read secrets only for comparison. Never print them or write them to a report.
for (const path of ['frontend/.env.local', 'agent/.env.local', 'agent/.env']) {
  const fullPath = join(root, path);
  if (!existsSync(fullPath)) continue;
  for (const line of readFileSync(fullPath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*(?:export\s+)?([A-Z_]*(?:API_KEY|API_SECRET))\s*=\s*(.*?)\s*$/);
    if (match) {
      const value = match[2].replace(/^['"]|['"]$/g, '');
      if (value.length >= 12) values.add(value);
    }
  }
}
for (const name of ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'ANAM_API_KEY']) {
  if (process.env[name]?.length >= 12) values.add(process.env[name]);
}
assert.ok(
  values.size,
  'Supply local credentials or environment variables for the leak comparison.'
);
const excluded = new Set([
  '.git',
  'node_modules',
  '.next',
  '.next-vercel-check',
  '.local-test-cache',
  '.venv',
  '.tools',
  '.python',
  '.uv-cache',
  '__pycache__',
  '.pytest_cache',
  '.ruff_cache',
  'test-results',
  'artifacts',
]);
let checked = 0;
const leaks = [];
function scan(directory, clientBundle = false) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory()) {
      if (
        !excluded.has(entry.name) &&
        !entry.name.startsWith('.next') &&
        !entry.name.endsWith('.egg-info')
      )
        scan(path, clientBundle);
    } else if (
      (!entry.name.startsWith('.env') || entry.name === '.env.example') &&
      /\.(?:ts|tsx|js|mjs|cjs|json|md|yml|yaml|toml|py|txt|example)$/.test(entry.name)
    ) {
      const content = readFileSync(path, 'utf8');
      checked++;
      if ([...values].some((secret) => content.includes(secret))) leaks.push(path);
      if (!clientBundle && path.endsWith('.env.example')) {
        assert.ok(
          !/^[ \t]*\w*(?:API_KEY|API_SECRET)[ \t]*=[ \t]*[^ \t\r\n]+/m.test(content),
          'Example contains credentials.'
        );
      }
    }
  }
}
scan(root);
const bundle = resolve(frontend, process.env.FRONTEND_BUILD_DIR || '.next', 'static');
if (existsSync(bundle)) scan(bundle, true);
assert.equal(
  leaks.length,
  0,
  `Known credentials found in source or client bundles: ${leaks.join(', ')}`
);
console.log(
  `PASS: ${checked} source/client files checked; no configured API credentials found. Values hidden.`
);
