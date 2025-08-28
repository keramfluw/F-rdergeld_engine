#!/usr/bin/env bash
set -euo pipefail
export FT_RADAR_DB_PATH="data/radar.db"
python3 admin/ingest.py init-db
python3 admin/ingest.py import-json data/seed/seed_items.json
python3 admin/publish_digest.py
