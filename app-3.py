# app.py — Fördergeld Engine (minimal funktionsfähig)
# Hinweis: bewusst keine externen Abhängigkeiten außer streamlit & pandas.
# Start lokal: `streamlit run app.py`

import streamlit as st
import pandas as pd
from math import isnan

st.set_page_config(page_title="Fördergeld Engine", page_icon="💶", layout="wide")

# ---------------------------
# Hilfsfunktionen
# ---------------------------
def eur_de(value: float | int) -> str:
    try:
        s = f"{float(value):,.2f}"
    except Exception:
        return "—"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"

def annuity(pv: float, apr: float, years: int) -> float:
    """Monatliche Rate einer Annuität (vereinfacht, konstante Zahlungen). apr als Dezimalzahl z. B. 0.03 für 3%"""
    if apr is None or years is None or years <= 0:
        return float("nan")
    i = apr / 12
    n = years * 12
    if i == 0:
        return pv / n
    return pv * (i * (1 + i) ** n) / ((1 + i) ** n - 1)

def effective_monthly_benefit(grant_amount: float, loan_saving_per_month: float | None = None) -> float:
    """Schätzt einen 'monatlichen Nutzen': Zuschuss linear über 10 Jahre verteilt + ggf. Zinsvorteil pro Monat."""
    # Vereinfachte, konservative Darstellung: Zuschuss über 120 Monate verteilt
    z = (grant_amount or 0) / 120.0
    l = loan_saving_per_month or 0
    return z + l

# ---------------------------
# Beispiel-Programmdaten (Platzhalter; bitte mit echten Programmdaten ersetzen)
# ---------------------------
PROGRAMS = [
    {
        "id": "BAFA-WP-2025",
        "name": "BAFA – Bundesförderung effiziente Gebäude (BEG) – Einzelmaßnahmen Wärmepumpe",
        "agency": "BAFA",
        "instrument": "Zuschuss",
        "tech": ["Wärmepumpe"],
        "sector": ["Wohnungswirtschaft", "Gewerbe/Industrie"],
        "bundeslaender": ["Alle"],
        "grant_rate": 0.25,
        "grant_cap": 30000,  # EUR
        "loan_apr": None,
        "loan_term_years": None,
        "source": "https://www.bafa.de/DE/Energie/BEG/EM/Heizung/heizung_node.html",
    },
    {
        "id": "KfW-270-2025",
        "name": "KfW 270 – Erneuerbare Energien – Standard (PV & Speicher)",
        "agency": "KfW",
        "instrument": "Kredit",
        "tech": ["PV", "Speicher"],
        "sector": ["Wohnungswirtschaft", "Gewerbe/Industrie", "Kommunen"],
        "bundeslaender": ["Alle"],
        "grant_rate": 0.0,
        "grant_cap": 0,
        # Beispielhafter Nominalzins; echte Konditionen bitte prüfen
        "loan_apr": 0.03,
        "loan_term_years": 10,
        "source": "https://www.kfw.de/270/",
    },
    {
        "id": "Land-BW-PV-2025",
        "name": "Landesprogramm BW – PV auf Mehrfamilienhäusern (Beispiel)",
        "agency": "MWK/Landesbank",
        "instrument": "Zuschuss",
        "tech": ["PV"],
        "sector": ["Wohnungswirtschaft"],
        "bundeslaender": ["Baden-Württemberg"],
        "grant_rate": 0.10,
        "grant_cap": 50000,
        "loan_apr": None,
        "loan_term_years": None,
        "source": "https://www.baden-wuerttemberg.de",
    },
]

# ---------------------------
# UI – Sidebar Eingaben
# ---------------------------
st.sidebar.header("Projekt-Parameter")
bundesland = st.sidebar.selectbox(
    "Bundesland",
    options=sorted({b for p in PROGRAMS for b in (p["bundeslaender"] if p["bundeslaender"] != ["Alle"] else ["Alle"])}),
    index=0,
)
sector = st.sidebar.multiselect(
    "Sektor(e)",
    options=sorted({s for p in PROGRAMS for s in p["sector"]}),
    default=["Wohnungswirtschaft"],
)
tech = st.sidebar.multiselect(
    "Technologie(n)",
    options=sorted({t for p in PROGRAMS for t in p["tech"]}),
    default=["PV", "Speicher"],
)
capex = st.sidebar.number_input("Investitionssumme (EUR)", min_value=0.0, step=1000.0, value=120000.0)
year = st.sidebar.number_input("Inbetriebnahme-/Bewilligungsjahr", min_value=2024, max_value=2030, step=1, value=2025)
st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Beispielhafte, nicht rechtsverbindliche Darstellung. Prüfen Sie stets die Originalquellen.")

st.title("💶 Fördergeld Engine – Übersicht möglicher Förderoptionen")
st.write("Qrauts AG 2025 developed by MW")

# ---------------------------
# Filter + Berechnung
# ---------------------------
def program_matches(p) -> bool:
    if bundesland != "Alle" and "Alle" not in p["bundeslaender"] and bundesland not in p["bundeslaender"]:
        return False
    if sector and not any(s in p["sector"] for s in sector):
        return False
    if tech and not any(t in p["tech"] for t in tech):
        return False
    return True

def compute_table(capex_value: float) -> pd.DataFrame:
    rows = []
    for p in PROGRAMS:
        if not program_matches(p):
            continue

        grant_amount = min(capex_value * p["grant_rate"], p["grant_cap"]) if p["instrument"] == "Zuschuss" else 0.0
        monthly_loan_rate = annuity(capex_value, p["loan_apr"], p["loan_term_years"]) if p["instrument"] == "Kredit" else float("nan")

        # *price_eur_per_month* als generische, im UI verwendete Anzeige (z. B. 'monatlicher Nutzen')
        price_eur_per_month = effective_monthly_benefit(grant_amount, loan_saving_per_month=None)

        rows.append({
            "Programm-ID": p["id"],
            "Programm": p["name"],
            "Träger": p["agency"],
            "Instrument": p["instrument"],
            "Tech": ", ".join(p["tech"]),
            "Fördersatz": f"{int(p['grant_rate']*100)} %" if p["grant_rate"] else "—",
            "Zuschuss (geschätzt)": grant_amount,
            "Kredit-Rate/Monat (geschätzt)": monthly_loan_rate,
            "price_eur_per_month": price_eur_per_month,
            "Quelle": p["source"],
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Zuschuss (geschätzt)"] = df["Zuschuss (geschätzt)"].apply(eur_de)
        df["Kredit-Rate/Monat (geschätzt)"] = df["Kredit-Rate/Monat (geschätzt)"].apply(lambda x: eur_de(x) if x==x else "—")
        df["Monatlicher Nutzen (heuristisch)"] = df["price_eur_per_month"].apply(eur_de)
        df = df.drop(columns=["price_eur_per_month"])
    return df

df = compute_table(capex)

# ---------------------------
# Ausgabe
# ---------------------------
if df.empty:
    st.info("Keine Programme gefunden. Passen Sie die Filter an.")
else:
    st.subheader("Gefilterte Programme")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export (CSV, um Zusatz-Abhängigkeiten zu vermeiden)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("CSV exportieren", csv, file_name="foerderprogramm_ergebnis.csv", mime="text/csv")

st.markdown("---")
with st.expander("⚙️ Hinweise & Nächste Schritte"):
    st.markdown("""
- **Ersetzen Sie die Platzhalterdaten** durch echte Programmspezifika (Zuschusssätze, Deckelungen, Antragsfristen),
  z. B. aus KfW-/BAFA-/Landesseiten.
- **Validieren Sie Konditionen** (Zinssätze, Laufzeiten) vor jeder Nutzung.
- **Erweitern Sie die Logik**: differenzierte Berechnung je Programm, Stichtage, Kumulierung, De-minimis, etc.
- **Auditierbarkeit**: versionieren Sie Programmdaten (CSV/JSON) und hinterlegen Sie Quell-URLs + Abrufdatum.
""")
