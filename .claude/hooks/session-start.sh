#!/bin/bash
# Installs Headroom + Graphify and starts the Headroom proxy at every session start (cloud only).
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
export PATH="$HOME/.local/bin:$PATH"
cd "${CLAUDE_PROJECT_DIR:-.}"

if ! ls "$(uv tool dir)"/headroom-ai/lib/python*/site-packages/fastapi >/dev/null 2>&1; then uv tool install --force --python 3.13 "headroom-ai[proxy]"; fi
command -v graphify >/dev/null || uv tool install --python 3.13 "graphifyy[mcp]"

# Graphify skill for Claude (idempotent)
[ -d "$HOME/.claude/skills/graphify" ] || graphify install --platform claude >/dev/null 2>&1 || true

# Headroom proxy in background on 8787 (skip if already up)
if ! (exec 3<>/dev/tcp/127.0.0.1/8787) 2>/dev/null; then
  nohup headroom proxy --port 8787 >/tmp/headroom-proxy.log 2>&1 &
  disown || true
fi

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
