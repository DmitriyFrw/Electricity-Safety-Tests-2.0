#!/usr/bin/env bash
# Синхронизация макета razvivaisia → React frontend
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cp "$ROOT/razvivaisia/css/"*.css "$ROOT/frontend/src/styles/razvivaisia/"
cp "$ROOT/razvivaisia/js/main.js" "$ROOT/frontend/public/razvivaisia/main.js"
cp "$ROOT/razvivaisia/"*.html "$ROOT/frontend/public/razvivaisia/" 2>/dev/null || true
if [ -d "$ROOT/razvivaisia/assets" ]; then
  mkdir -p "$ROOT/frontend/public/razvivaisia/assets"
  cp -R "$ROOT/razvivaisia/assets/." "$ROOT/frontend/public/razvivaisia/assets/"
fi

echo "OK: razvivaisia → frontend"
