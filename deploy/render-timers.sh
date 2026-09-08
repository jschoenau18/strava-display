#!/usr/bin/env bash
# Renders deploy/*.timer.template into deploy/*.timer using the interval
# values from .env (STRAVA_UPDATE_INTERVAL_MIN / STRAVA_DISPLAY_CYCLE_INTERVAL_MIN),
# since systemd timers can't read .env themselves - OnUnitActiveSec is a
# static value in the unit file.
#
# Run this after changing either variable in .env, then re-copy the
# regenerated .timer files to /etc/systemd/system and reload:
#
#   deploy/render-timers.sh
#   sudo cp deploy/strava-dashboard.timer deploy/strava-display-cycle.timer /etc/systemd/system/
#   sudo systemctl daemon-reload
set -euo pipefail
cd "$(dirname "$0")/.."

UPDATE_INTERVAL_MIN="$(grep -E '^STRAVA_UPDATE_INTERVAL_MIN=' .env 2>/dev/null | tail -n1 | cut -d= -f2-)"
DISPLAY_CYCLE_INTERVAL_MIN="$(grep -E '^STRAVA_DISPLAY_CYCLE_INTERVAL_MIN=' .env 2>/dev/null | tail -n1 | cut -d= -f2-)"

UPDATE_INTERVAL_MIN="${UPDATE_INTERVAL_MIN:-10}"
DISPLAY_CYCLE_INTERVAL_MIN="${DISPLAY_CYCLE_INTERVAL_MIN:-2}"

sed "s/@INTERVAL_MIN@/${UPDATE_INTERVAL_MIN}/g" deploy/strava-dashboard.timer.template > deploy/strava-dashboard.timer
sed "s/@INTERVAL_MIN@/${DISPLAY_CYCLE_INTERVAL_MIN}/g" deploy/strava-display-cycle.timer.template > deploy/strava-display-cycle.timer

echo "Rendered deploy/strava-dashboard.timer (every ${UPDATE_INTERVAL_MIN} min) and deploy/strava-display-cycle.timer (every ${DISPLAY_CYCLE_INTERVAL_MIN} min)."
