#!/usr/bin/env bash
# Checks GitHub for a newer release tag and, if found, checks it out and
# reinstalls dependencies. Run nightly via strava-update.timer.
set -euo pipefail

REPO_DIR="/home/jschoenau/strava-api-display"
cd "$REPO_DIR"

git fetch --tags --prune origin

current_tag="$(git describe --tags --abbrev=0 2>/dev/null || echo "<none>")"
latest_tag="$(git tag --list 'v*' --sort=-v:refname | head -n1)"

if [[ -z "$latest_tag" ]]; then
    echo "No version tags found on origin, nothing to do."
    exit 0
fi

if [[ "$latest_tag" == "$current_tag" ]]; then
    echo "Already on latest release ($current_tag)."
    exit 0
fi

echo "New release found: ${current_tag} -> ${latest_tag}. Updating..."
git checkout "$latest_tag"
.venv/bin/pip install -r requirements.txt

echo "Update complete, now at $latest_tag. Triggering dashboard refresh..."
GPIOZERO_PIN_FACTORY=lgpio \
PYTHONPATH=/home/jschoenau/e-Paper/E-paper_Separate_Program/4inch_e-Paper_E/RaspberryPi_JetsonNano/python/lib \
"$REPO_DIR/.venv/bin/python" main.py

echo "Note: if deploy/strava-dashboard.service or .timer changed in this release, re-copy them to /etc/systemd/system and run 'sudo systemctl daemon-reload' manually."
