param(
    [ValidateSet('setup', 'dev', 'console', 'start', 'check', 'test', 'evaluate')]
    [string]$Mode = 'dev'
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.python'
    $env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.uv-cache'
    $localUv = Join-Path $PSScriptRoot '.tools/uv.exe'
    $uv = if (Test-Path -LiteralPath $localUv) { $localUv } else { 'uv' }

    if ($Mode -eq 'setup') {
        & $uv sync --locked
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        if (!(Test-Path -LiteralPath '.env.local')) {
            Copy-Item -LiteralPath '.env.example' -Destination '.env.local'
        }
        & $uv run --module livekit.agents download-files
    } elseif ($Mode -eq 'check') {
        & $uv run ruff format --check src tests scripts
        if ($LASTEXITCODE -ne 0) { throw 'Formatting check failed.' }
        & $uv run ruff check src tests scripts
        if ($LASTEXITCODE -ne 0) { throw 'Lint check failed.' }
        & $uv run src/agent.py --help
    } elseif ($Mode -eq 'test') {
        & $uv run pytest -q
    } elseif ($Mode -eq 'evaluate') {
        & $uv run python scripts/evaluate.py
    } else {
        $credentials = Get-Content -LiteralPath '.env.local' -ErrorAction SilentlyContinue
        foreach ($name in @('LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET')) {
            if (![Environment]::GetEnvironmentVariable($name) -and
                !($credentials -match "^\s*$name\s*=\s*[^\s#]+")) {
                throw "Set $name in agent/.env.local or your environment before starting."
            }
        }
        & $uv run src/agent.py $Mode
    }
    if ($LASTEXITCODE -ne 0) { throw "Agent command failed with exit code $LASTEXITCODE." }
} finally {
    Pop-Location
}
