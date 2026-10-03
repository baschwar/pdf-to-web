#!/bin/zsh

set -u

# Finder launches may inherit only the system paths. Include both standard
# Homebrew locations so installed Poppler utilities are available to the app.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR" || exit 1

if [[ ! -x ".venv/bin/pdf-to-web" ]]; then
  echo "PDF to Web is not set up in this folder."
  echo
  echo "Follow the Development setup steps in README.md, then launch this file again."
  echo
  read -k 1 "?Press any key to close."
  echo
  exit 1
fi

echo "Starting PDF to Web..."
echo "Leave this window open while using the application."
echo

exec .venv/bin/pdf-to-web serve
