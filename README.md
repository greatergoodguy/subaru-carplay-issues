# Subaru CarPlay & Infotainment Issues

A public, searchable record of NHTSA owner complaints about head unit failures in 2019–2023 Subaru vehicles (CarPlay/Android Auto disconnects, USB dropouts, Bluetooth failures, black or rebooting screens), alongside Subaru's own technical service bulletins.

Live site: https://greatergoodguy.github.io/subaru-carplay-issues/

Independent owner project. Not affiliated with Subaru of America, Inc. or Subaru Corporation.

## How it's built

- `data/complaints.json`: NHTSA complaints (public records), each individually reviewed and tagged by symptom.
- `scripts/build.py`: generates the static pages (`python3 scripts/build.py`).
- Hosted on GitHub Pages; no server, no tracking.

Corrections: open an issue.
