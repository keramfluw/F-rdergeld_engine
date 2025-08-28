# Förder- & Tarif-Radar (MVP) – Wulff technologies Branding

Ein minimales, **produktisiertes** Startpaket für einen kuratierten Radar rund um **Förderungen, Tarife und Regulatorik**.
Branding & Farbschema: Wulff technologies (Neon Blue, Cyber Black, Futuristic Red).

## Schnellstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export FT_RADAR_DB_PATH="data/radar.db"
python admin/ingest.py init-db
python admin/ingest.py import-json data/seed/seed_items.json

export FT_RADAR_ACCESS_CODE="CHANGEME-ACCESS"
streamlit run app/app.py
```

## Preisliste (konkret)
| Tier   | Preis/Monat | Kern-Features |
|--------|-------------:|---------------|
| Starter | 99 € (zzgl. USt.) | Kuratierter Feed, wöchentlicher Digest (1 Empfänger), 1 Nutzer/Team, Filter & CSV/MD-Export |
| Team    | 249 € (zzgl. USt.) | Alles aus Starter, bis 10 Empfänger, 5 Nutzer, Basis-API (5k Calls/Monat), priorisierte Quellen & Alerts, Support NBD |
| Pro     | 499 € (zzgl. USt.) | Alles aus Team, White-Label & PDF-Report, erweiterte API/Webhooks (50k Calls/Monat), SLA 99.9%, priorisierter Support |

> Hinweis: Preise für MVP/Frühbucher. Individuelle Konditionen/Enterprise auf Anfrage.

## Branding
- **Logo**: `branding/assets/wulff_logo.png`
- **Palette**: Futuristic Red `#FF0033`, Cyber Black `#0A0A0A`, Neon Blue `#00FFFF`, Tech Grey `#888C8F`, Pure White `#FFFFFF`
- Streamlit-Theme: `.streamlit/config.toml`, zusätzliche CSS-Variablen in `app/app.py`.

## Recht & Ethik
- **Disclaimer**: Keine Rechts-/Steuerberatung. Quellen stets prüfen.
- **Datenschutz**: Keine personenbezogenen Daten speichern; Logs minimieren.
