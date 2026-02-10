#!/usr/bin/env bash
# =========================================================
# sshx v1.1 — Simple SSH Manager (ZERO-RC, Binary Safe)
# Author: Sumit
# =========================================================

VERSION="1.1"
CACHE="$HOME/.ssh/sshx.json"
KEY="$HOME/.ssh/id_ed25519"

GREEN="\e[32m"; RED="\e[31m"; YELLOW="\e[33m"; BLUE="\e[34m"; NC="\e[0m"

die()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

need() { command -v "$1" &>/dev/null || die "$1 not installed"; }

# ================= INIT =================
init() {
  mkdir -p "$HOME/.ssh"
  [ -f "$CACHE" ] || echo "{}" > "$CACHE"

  if [ ! -f "$KEY" ]; then
    info "Generating SSH key..."
    ssh-keygen -t ed25519 -f "$KEY" -N "" || die "ssh-keygen failed"
  fi

  chmod 600 "$KEY" 2>/dev/null || true
}

# ========== ZERO-RC DYNAMIC COMPLETION ==========
# bash calls: sshx __complete__ <words…>
if [[ "$1" == "__complete__" ]]; then
  echo "--add"
  echo "--remove"
  echo "--list"
  echo "--menu"
  echo "--doctor"
  echo "--help"
  echo "--version"
  jq -r 'keys[]' "$CACHE" 2>/dev/null
  exit 0
fi

# Register completion silently (no rc, no files)
complete -C sshx sshx 2>/dev/null || true

# ================= PARSE =================
parse() {
  if [[ "$1" == *"@"*":"* ]]; then
    USER="${1%@*}"
    HOST="${1#*@}"
    HOST="${HOST%:*}"
    PORT="${1##*:}"
  else
    USER="$1"; HOST="$2"; PORT="$3"
  fi

  [ -z "$USER" ] || [ -z "$HOST" ] || [ -z "$PORT" ] && die "Invalid format. Use user@ip:port"
}

exists() {
  jq -e ".\"$USER@$HOST:$PORT\"" "$CACHE" >/dev/null 2>&1
}

# ================= ACTIONS =================
add() {
  exists && warn "Already added. Use --remove first." && exit 0

  info "Testing connection (may ask password once)..."
  timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=5 -p "$PORT" "$USER@$HOST" exit \
    || warn "Password will be required once"

  ssh-copy-id -i "$KEY.pub" -p "$PORT" "$USER@$HOST" || die "Key copy failed"

  jq ". + {\"$USER@$HOST:$PORT\": {user:\"$USER\",host:\"$HOST\",port:$PORT}}" \
    "$CACHE" > "$CACHE.tmp" && mv "$CACHE.tmp" "$CACHE"

  ok "Added successfully (passwordless enabled)"
}

connect() {
  exists || die "Host not added. Run: sshx $USER@$HOST:$PORT --add"
  ssh -p "$PORT" "$USER@$HOST"
}

remove() {
  exists || die "Entry not found"
  jq "del(.\"$USER@$HOST:$PORT\")" "$CACHE" > "$CACHE.tmp" && mv "$CACHE.tmp" "$CACHE"
  ok "Removed entry"
}

list() {
  jq -r 'keys[]' "$CACHE" 2>/dev/null || echo "(empty)"
}

fzf_menu() {
  need fzf
  sel=$(list | fzf --prompt="SSH > ")
  [ -z "$sel" ] && exit 0
  sshx "$sel"
}

doctor() {
  echo "sshx v$VERSION"
  need ssh
  need jq
  command -v fzf &>/dev/null && ok "fzf installed" || warn "fzf missing"
  [ -f "$KEY" ] && ok "SSH key exists" || warn "SSH key missing"
  stat -c "%a" "$KEY" 2>/dev/null | grep -q 600 \
    && ok "Key permission OK" || warn "Key permission should be 600"
}

help() {
cat <<EOF
sshx v$VERSION — Simple SSH Manager

USAGE:
  sshx user@ip:port --add       Add host & copy key
  sshx user@ip:port             Connect (passwordless)
  sshx user@ip:port --remove    Remove entry

OTHER:
  sshx --list                   List saved hosts
  sshx --menu                   fzf interactive menu
  sshx --doctor                 Self check
  sshx --version | -v
  sshx --help | -h

FEATURES:
  🔑 Auto ssh-keygen
  🔐 Auto key permission fix
  📋 Passwordless SSH
  🎯 fzf menu
  🧠 History based autocomplete
  🗂 ~/.ssh/sshx.json cache
  🧼 ZERO-RC / Binary safe
EOF
}

# ================= MAIN =================
init

case "$1" in
  --help|-h|help) help ;;
  --version|-v|version) echo "sshx v$VERSION" ;;
  --list) list ;;
  --menu) fzf_menu ;;
  --doctor) doctor ;;
  *)
    parse "$@"
    case "$2" in
      --add) add ;;
      --remove) remove ;;
      "") connect ;;
      *) help ;;
    esac
  ;;
esac
