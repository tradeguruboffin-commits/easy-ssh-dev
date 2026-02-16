#!/usr/bin/env bash
# =========================================================
# easy-ssh-dev — Dependency Installer (CLI + GUI + Build)
# Release Candidate v1.1
# Author: Sumit
# =========================================================

set -Eeuo pipefail
IFS=$'\n\t'
trap 'rc=$?; echo -e "${RED}❌ Error on line $LINENO (exit $rc)${NC}"; exit $rc' ERR

# ---------------- Colors ----------------

RED="\e[31m"; GREEN="\e[32m"; YELLOW="\e[33m"
BLUE="\e[34m"; CYAN="\e[36m"; NC="\e[0m"

log()  { echo -e "${CYAN}➜${NC} $*"; }
ok()   { echo -e "${GREEN}✔${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✖${NC} $*"; }

# ---------------- Config ----------------

VERSION="1.1-rc"
PY_MIN_MAJOR=3
PY_MIN_MINOR=8
GO_MIN_MAJOR=1
GO_MIN_MINOR=20

DRY_RUN=false
AUTO_YES=false
AUTO_BUILD=false

# ---------------- Args ----------------

usage() {
  echo "easy-ssh-dev Installer v$VERSION"
  echo ""
  echo "Usage: $0 [options]"
  echo "  --dry-run       Show actions only"
  echo "  -y, --yes       Auto confirm"
  echo "  --build         Install build deps"
  echo "  -h, --help      Show help"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    -y|--yes)  AUTO_YES=true ;;
    --build)   AUTO_BUILD=true ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown option: $1"; usage; exit 1 ;;
  esac
  shift
done

run() {
  log "$*"
  [[ "$DRY_RUN" == true ]] && return 0
  "$@"
}

confirm() {
  [[ "$AUTO_YES" == true ]] && return 0
  read -rp "Continue? [y/N]: " ans
  [[ "${ans,,}" == "y" ]]
}

# ---------------- Root ----------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}🔧 easy-ssh-dev Dependency Installer v$VERSION${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "----------------------------------------"

# ---------------- OS Detect ----------------

OS=""; PM=""; SUDO=""

if [[ -n "${TERMUX_VERSION:-}" ]]; then
  OS=termux; PM=pkg
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS=macos; PM=brew
elif command -v apt >/dev/null; then
  OS=debian; PM=apt
elif command -v dnf >/dev/null; then
  OS=fedora; PM=dnf
elif command -v pacman >/dev/null; then
  OS=arch; PM=pacman
elif command -v apk >/dev/null; then
  OS=alpine; PM=apk
else
  err "Unsupported OS"
  exit 1
fi

[[ "$EUID" -ne 0 && -x "$(command -v sudo)" ]] && SUDO=sudo

echo "OS: $OS | Package Manager: $PM"
echo "----------------------------------------"

# ---------------- Version Checks ----------------

check_python() {
  command -v python3 >/dev/null || return 1
  python3 - <<EOF
import sys
sys.exit(0 if sys.version_info >= ($PY_MIN_MAJOR,$PY_MIN_MINOR) else 1)
EOF
}

check_go() {
  command -v go >/dev/null || return 1
  ver=$(go env GOVERSION 2>/dev/null || go version | awk '{print $3}')
  ver="${ver#go}"
  IFS=. read -r major minor _ <<< "$ver"
  (( major > GO_MIN_MAJOR || (major == GO_MIN_MAJOR && minor >= GO_MIN_MINOR) ))
}

# ---------------- Installer ----------------

install_pkgs() {
  case "$PM" in
    apt)
      run $SUDO apt update
      run $SUDO apt install -y "$@"
      ;;
    dnf)
      run $SUDO dnf install -y "$@"
      ;;
    pacman)
      run $SUDO pacman -Syu --noconfirm "$@"
      ;;
    apk)
      run $SUDO apk add "$@"
      ;;
    pkg)
      run pkg update -y
      run pkg install -y "$@"
      ;;
    brew)
      run brew update
      run brew install "$@"
      ;;
  esac
}

# ---------------- Dependency Matrix ----------------

case "$OS" in
debian)
  CORE=(golang-go python3 python3-venv python3-pip jq openssh-client)
  GUI_DEPS=(libgtk-3-0 gir1.2-gtk-3.0 libvte-2.91-0 gir1.2-vte-2.91 python3-gi python3-gi-cairo)
  BUILD_DEPS=(binutils build-essential python3-pyinstaller)
;;
fedora)
  CORE=(golang python3 python3-pip jq openssh-clients)
  GUI_DEPS=(gtk3 vte291 python3-gobject cairo-gobject)
  BUILD_DEPS=(binutils gcc gcc-c++ make python3-pyinstaller)
;;
arch)
  CORE=(go python jq openssh python-virtualenv)
  GUI_DEPS=(gtk3 vte3 python-gobject python-cairo)
  BUILD_DEPS=(binutils base-devel python-pyinstaller)
;;
alpine)
  CORE=(go python3 py3-pip py3-virtualenv jq openssh)
  GUI_DEPS=(gtk+3.0 vte3 py3-gobject3 py3-cairo)
  BUILD_DEPS=(binutils build-base py3-pyinstaller)
;;
termux)
  CORE=(go python jq openssh)
  GUI_DEPS=()
  BUILD_DEPS=(binutils)
;;
macos)
  CORE=(go python jq)
  GUI_DEPS=(gtk+3 vte3 pygobject3)
  BUILD_DEPS=(pyinstaller)
;;
esac

# ---------------- Install Flow ----------------

echo "Checking core dependencies..."
NEED=false

if ! check_python; then
  warn "Python >= ${PY_MIN_MAJOR}.${PY_MIN_MINOR} required"
  NEED=true
fi

if ! check_go; then
  warn "Go >= ${GO_MIN_MAJOR}.${GO_MIN_MINOR} required"
  NEED=true
fi

for cmd in jq ssh; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    warn "$cmd missing"
    NEED=true
  fi
done

if [[ "$NEED" == true ]]; then
  warn "Core dependencies missing"
  confirm || exit 1
  install_pkgs "${CORE[@]}"
else
  ok "Core dependencies OK"
fi

echo "Installing GUI dependencies..."
[[ "${#GUI_DEPS[@]}" -gt 0 ]] && install_pkgs "${GUI_DEPS[@]}"

if [[ "$AUTO_BUILD" == true ]]; then
  echo "Installing build dependencies..."
  install_pkgs "${BUILD_DEPS[@]}"
fi

# ---------------- Final Build Trigger (Always) ----------------

echo ""
echo "----------------------------------------"
log "Triggering build step..."

if [[ -f "$PROJECT_ROOT/app-build-install" ]]; then
  if [[ "$DRY_RUN" == true ]]; then
    log "[DRY RUN] Would execute: bash $PROJECT_ROOT/app-build-install"
  else
    bash "$PROJECT_ROOT/app-build-install" || warn "Build step failed (installer completed)"
  fi
else
  warn "app-build-install not found — skipping build step"
fi

# ---------------- Finish ----------------

echo "----------------------------------------"
echo "Log file: $LOG_FILE"
ok "ALL DONE SUCCESSFULLY 🚀"
