#!/usr/bin/env bash
# Checks GitHub for a newer release tag and, if found, checks it out,
# reinstalls dependencies and verifies the new release actually runs before
# considering the update successful. If verification fails, rolls back to
# the previous tag so the Pi never gets stuck on a broken release.
# Run nightly via strava-update.timer.
set -uo pipefail

REPO_DIR="/home/jschoenau/strava-api-display"
EPAPER_PYTHONPATH="/home/jschoenau/e-Paper/E-paper_Separate_Program/4inch_e-Paper_E/RaspberryPi_JetsonNano/python/lib"
cd "$REPO_DIR"

run_dashboard() {
    # flock serializes against strava-dashboard.timer / other concurrent runs -
    # both touch the same e-paper GPIO pins, and a second process claiming an
    # already-held pin crashes with "lgpio.error: 'GPIO busy'" instead of waiting.
    GPIOZERO_PIN_FACTORY=lgpio PYTHONPATH="$EPAPER_PYTHONPATH" \
        flock -w 60 "$REPO_DIR/.dashboard.lock" "$REPO_DIR/.venv/bin/python" main.py
}

rollback_to() {
    local tag="$1"
    echo "Rolling back to $tag..." >&2
    git checkout "$tag" && .venv/bin/pip install -r requirements.txt
}

if ! git fetch --tags --prune origin; then
    echo "git fetch failed, aborting." >&2
    exit 1
fi

previous_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
# Only real releases (vX.Y.Z) are auto-pulled - tags with a suffix like
# "-pre" (e.g. v1.2.0-pre) are pre-releases for manual testing and must
# never be picked up automatically.
latest_tag="$(git tag --list 'v*' --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n1)"

if [[ -z "$latest_tag" ]]; then
    echo "No version tags found on origin, nothing to do."
    exit 0
fi

if [[ "$latest_tag" == "$previous_tag" ]]; then
    echo "Already on latest release (${previous_tag})."
    exit 0
fi

echo "New release found: ${previous_tag:-<none>} -> ${latest_tag}. Updating..."

if ! git checkout "$latest_tag" || ! .venv/bin/pip install -r requirements.txt; then
    echo "Checkout or dependency install for $latest_tag failed." >&2
    [[ -n "$previous_tag" ]] && rollback_to "$previous_tag"
    exit 1
fi

echo "Verifying $latest_tag by rendering the dashboard..."
if ! run_dashboard; then
    echo "Dashboard run on $latest_tag failed - new release is broken." >&2
    if [[ -n "$previous_tag" ]]; then
        rollback_to "$previous_tag" && run_dashboard
    fi
    exit 1
fi

echo "Update complete and verified, now at $latest_tag."
echo "Note: if deploy/strava-dashboard.service or .timer changed in this release, re-copy them to /etc/systemd/system and run 'sudo systemctl daemon-reload' manually."
