# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.
Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [1.2.0] - 2026-09-05

### Hinzugefügt

- Dark Mode (`STRAVA_DARK_MODE=1` in `.env`): schwarzer statt weißer
  Hintergrund, Text/Linien/Icons/Logo in Weiß statt Schwarz; Strava-Orange
  und die übrigen Akzentfarben der Palette bleiben unverändert.
- Persistentes Log (`strava-display.log`) für beide systemd-Services, mit
  Zeitstempel-Header pro Lauf; `deploy/strava-display.logrotate` hält
  jeweils höchstens den aktuellen plus den letzten Tag vor.
- Failsafe in `display/eink.py`: prüft vor dem Panel-Zugriff, ob
  `/dev/spidev*` existiert, und bricht mit einer klaren Fehlermeldung ab,
  statt bei nicht aktiviertem SPI unbegrenzt auf den BUSY-Pin zu warten.

### Geändert

- Der manuelle Testlauf-Befehl für `main.py` in der README nutzt jetzt
  denselben `flock` wie die systemd-Units, um Races mit einem parallel
  laufenden Timer-Job zu vermeiden.

### Behoben

- Dashboard-PNGs und der Wetter-Standort-Cache werden jetzt atomar
  geschrieben (Temp-Datei + `replace()`), damit ein gleichzeitiger
  Lesevorgang (z. B. `display_cycle.py` während eines manuellen, nicht
  geflockten `main.py`-Testlaufs) nie eine unvollständige Datei erwischt
  (`PIL.UnidentifiedImageError` bzw. `json.JSONDecodeError`).
- Ein defekter/leerer Wetter-Standort-Cache wird beim Lesen abgefangen
  statt den gesamten Lauf abzubrechen.
- `strava-update.service` setzte den Deploy-Key nicht: `Environment=GIT_SSH_COMMAND=ssh -i ... -o ...`
  war ohne Anführungszeichen angegeben, wodurch systemd den Wert am
  Leerzeichen in mehrere ungültige Einzel-Zuweisungen zerlegte
  (`GIT_SSH_COMMAND` landete nur bei `ssh`, ohne `-i <key>`) – der
  nächtliche Auto-Update-Timer schlug dadurch mit
  `git@github.com: Permission denied (publickey)` fehl.

## [1.1.0] - 2026-08-31

### Hinzugefügt

- Zweite Dashboard-Seite (Tabelle der letzten Aktivitäten + Monats-Kalender),
  im Wechsel mit Seite 1 über `display_cycle.py` (alle 2 Minuten) angezeigt.
- Schalter `STRAVA_SHOW_PAGE2` in `.env`, um Seite 2 komplett zu deaktivieren.
- Seite 1 zeigt links vom Titel ein Icon der Aktivitätsart (Rennrad/MTB/Lauf);
  zu lange Titel werden mit „…“ gekürzt.
- Eigene Kennzahlen für Läufe auf Seite 1: Distanz, Pace (min/km),
  Durchschnittspuls (neues Herz-Icon).
- Leistungs-Chips auf Seite 1 entfallen, wenn keine Power-Daten vorliegen (Lauf
  oder Ride ohne Power-Meter) – die Routen-Karte bekommt den freigewordenen
  Platz.
- Seiten-Indikator unten mittig, auf beiden Seiten an derselben Höhe
  ausgerichtet (unterer Rand der Höhengrafik von Seite 1).

### Geändert

- GPIO-Zugriff (Panel-Push) aus `main.py` in ein eigenes Skript
  `display_cycle.py` mit eigenem systemd-Timer `strava-display-cycle.timer`
  (alle 2 Minuten) ausgelagert; `main.py` rendert nur noch die PNGs.
- `deploy/update.sh` pullt nur noch echte `vX.Y.Z`-Release-Tags (keine
  `-pre`-Vorabversionen) und stößt nach dem Deploy zusätzlich
  `display_cycle.py` an, um das Panel sofort zu aktualisieren.

### Behoben

- Automatisches nächtliches Update (`strava-update.timer`) lief wegen
  fehlender Git-Auth-Konfiguration auf dem Pi nicht zuverlässig.

## [1.0.0] - 2026-08-25

### Hinzugefügt

- Automatisches nächtliches Deployment neuer Git-Tags auf dem Pi
  (`strava-update.timer` + `deploy/update.sh`) inklusive automatischem
  Rollback auf den letzten funktionierenden Tag bei Fehlern.
- Versions-Label im Dashboard (`backend/version.py`, aus dem aktuellen
  Git-Tag).
- `flock`-Sperre um alle E-Paper-GPIO-Zugriffe, um Abstürze durch
  gleichzeitige Läufe zu verhindern.

### Geändert

- Dokumentation für manuelle Git-Befehle (Deploy-Key-Auth) auf dem Pi
  ergänzt.

### Behoben

- Veraltete `Image.getdata`/`putdata`-Aufrufe in `image_cleanup` durch
  aktuelle Pillow-API ersetzt.

## [0.2.0] - 2026-08-24

### Hinzugefügt

- Wetter-Header (Temperatur, Wind, Niederschlagsprognose über Open-Meteo).
- Kudos-Anzeige, Höhenprofil-Grafik mit Anstiegs-Markierung, Wochen-Distanz-
  Balkendiagramm.
- Anzeige von Leistungsdaten (Durchschnittsleistung etc.).
- Fallback-Bild, falls keine Aktivitätsdaten gelesen werden können.

### Geändert

- Icons vergrößert, Höhenskala verschoben, Farbverlauf für Höhen-/
  Routen-Grafik angepasst.
- Update-Intervall auf 10 Minuten erhöht.

### Entfernt

- Erfundene „Best Powers“-Kennzahl entfernt (keine echten Daten dafür
  vorhanden).

## [0.1.0] - 2026-08-23

### Hinzugefügt

- Erste lauffähige Version: Strava-OAuth-Anbindung, Grundlayout des
  Dashboards (`GUIBox`, Dithering für die 6-Farb-Palette), Roboto-Fonts und
  Strava-Logo, `display/eink.py`-Treiber-Wrapper.

[Unreleased]: https://github.com/jschoenau18/strava-display/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/jschoenau18/strava-display/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/jschoenau18/strava-display/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jschoenau18/strava-display/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/jschoenau18/strava-display/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jschoenau18/strava-display/releases/tag/v0.1.0
