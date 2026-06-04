#!/usr/bin/env bash
# Копирует DejaVu TTF в app/static/fonts (системные пакеты или официальный архив).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${ROOT}/app/static/fonts"
mkdir -p "$DEST"

need=(
  DejaVuSans.ttf
  DejaVuSans-Bold.ttf
  DejaVuSans-Oblique.ttf
)

have_all=true
for f in "${need[@]}"; do
  if [[ ! -f "${DEST}/${f}" ]]; then
    have_all=false
    break
  fi
done
if $have_all; then
  echo "DejaVu fonts already present in ${DEST}"
  exit 0
fi

SYS_DIR="/usr/share/fonts/truetype/dejavu"
if [[ -d "${SYS_DIR}" ]]; then
  for f in "${need[@]}"; do
    if [[ -f "${SYS_DIR}/${f}" ]]; then
      cp "${SYS_DIR}/${f}" "${DEST}/"
    fi
  done
fi

have_all=true
for f in "${need[@]}"; do
  if [[ ! -f "${DEST}/${f}" ]]; then
    have_all=false
    break
  fi
done
if $have_all; then
  echo "DejaVu fonts installed from ${SYS_DIR}"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
ZIP="${TMP}/dejavu.zip"
URL="https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o "${ZIP}" "${URL}"
elif command -v wget >/dev/null 2>&1; then
  wget -q -O "${ZIP}" "${URL}"
else
  echo "Need curl or wget to download DejaVu fonts" >&2
  exit 1
fi

unzip -q -o "${ZIP}" -d "${TMP}/extract"
for f in "${need[@]}"; do
  found="$(find "${TMP}/extract" -name "${f}" -print -quit)"
  if [[ -z "${found}" ]]; then
    echo "Missing ${f} in DejaVu archive" >&2
    exit 1
  fi
  cp "${found}" "${DEST}/"
done

echo "DejaVu fonts downloaded to ${DEST}"
