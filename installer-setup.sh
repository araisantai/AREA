#!/usr/bin/env bash
# Install missing AREA V1 tools. Existing installations are preserved.
set -euo pipefail
CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=1
elif [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--check]" >&2
  exit 2
fi

find_tool() {
  if command -v "$1" >/dev/null 2>&1; then
    command -v "$1"
  elif [[ -x "$HOME/.local/bin/$1" ]]; then
    printf '%s\n' "$HOME/.local/bin/$1"
  else
    return 1
  fi
}

report() {
  local name="$1" path version
  path="$(find_tool "$name")"
  if [[ -z "$path" ]]; then
    echo "$name: missing"
    return 1
  fi
  version="$("$path" --version 2>&1 | head -n 1 || true)"
  echo "$name: $version ($path)"
  return 0
}

install_package() {
  local name="$1"
  if command -v brew >/dev/null 2>&1; then
    brew install "$name"
  elif command -v apt-get >/dev/null 2>&1; then
    local privilege=()
    if [[ "$EUID" -ne 0 ]]; then
      if ! command -v sudo >/dev/null 2>&1; then
        echo "sudo is required to install $name with apt-get" >&2
        return 1
      fi
      privilege=(sudo)
    fi
    "${privilege[@]}" apt-get update
    "${privilege[@]}" apt-get install -y "$name"
  else
    echo "No supported package manager found for $name (Homebrew or apt-get required)." >&2
    return 1
  fi
}

install_dirsearch() {
  if ! command -v python3 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
    echo 'dirsearch needs Python 3.11+ and git.' >&2
    return 1
  fi
  if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    echo 'dirsearch needs Python 3.11+.' >&2
    return 1
  fi
  if ! command -v pipx >/dev/null 2>&1; then
    install_package pipx
  fi
  pipx install 'git+https://github.com/maurosoria/dirsearch.git'
  echo 'dirsearch is available at ~/.local/bin/dirsearch; generated scripts find that path automatically.'
}

missing=()
for tool in nmap dirsearch feroxbuster; do
  if ! report "$tool"; then
    missing+=("$tool")
  fi
done
if [[ "$CHECK_ONLY" -eq 1 ]]; then
  if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "Missing: ${missing[*]}"
    exit 1
  fi
  exit 0
fi

for tool in "${missing[@]}"; do
  echo "Installing $tool..."
  case "$tool" in
    dirsearch) install_dirsearch ;;
    *) install_package "$tool" ;;
  esac
  report "$tool"
done
