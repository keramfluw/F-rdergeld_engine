
import os, sqlite3, datetime, pandas as pd, streamlit as st, yaml

st.set_page_config(page_title="Förder- & Tarif-Radar (MVP)", layout="wide")

APP_NAME = "Förder- & Tarif-Radar (MVP)"
DB_PATH = os.environ.get("FT_RADAR_DB_PATH", "data/radar.db")
ACCESS_CODE_ENV = os.environ.get("FT_RADAR_ACCESS_CODE", "")
DEFAULT_DAYS = int(os.environ.get("FT_RADAR_DEFAULT_DAYS", "14"))
LOGO_PATH = "branding/assets/wulff_logo.png"

# --- Styles (brand) ---
st.markdown("""
    <style>
      :root {
        --brand-primary: #00FFFF; /* Neon Blue */
        --brand-accent:  #FF0033; /* Futuristic Red */
        --brand-bg:      #0A0A0A; /* Cyber Black */
        --brand-muted:   #888C8F; /* Tech Grey */
        --brand-fg:      #FFFFFF; /* Pure White */
      }
      .radar-title { font-size: 26px; font-weight: 700; margin-bottom: 0.2rem; color: var(--brand-fg);}
      .radar-sub   { color: var(--brand-muted); margin-bottom: 1rem; }
      .radar-card { border: 1px solid var(--brand-muted); padding: 0.75rem 1rem; border-radius: 12px; margin-bottom: 0.75rem; background: rgba(255,255,255,0.02); }
      .radar-badge { background: var(--brand-accent); color: var(--brand-fg); padding: 2px 8px; border-radius: 999px; font-size: 12px; margin-right: 6px;}
      .price-card { border: 1px solid var(--brand-muted); border-radius: 14px; padding: 1rem; margin-bottom: 1rem; background: rgba(255,255,255,0.02);}
      .price-title{ font-size: 20px; font-weight: 700; color: var(--brand-primary); }
      .price-money{ font-size: 28px; font-weight: 800; color: var(--brand-fg); }
      .price-feat { color: var(--brand-fg); }
      .price-feat li { margin-bottom: 0.25rem; }
    </style>
""", unsafe_allow_html=True)

# --- Auth (simple shared access code) ---
def require_login():
    if os.environ.get("FT_RADAR_ALLOW_PUBLIC", "false").lower() == "true":
        return True
    if "logged_in" in st.session_state and st.session_state.logged_in:
        return True
    st.image(LOGO_PATH, width=140)
    st.markdown(f"<div class='radar-title'>{APP_NAME}</div>", unsafe_allow_html=True)
    st.markdown("<div class='radar-sub'>Bitte Zugangscode eingeben.</div>", unsafe_allow_html=True)
    code = st.text_input("Zugangscode", type="password")
    if st.button("Login"):
        if code and ACCESS_CODE_ENV and code == ACCESS_CODE_ENV:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Ungültiger Zugangscode.")
    st.stop()

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    return con

def ensure_db():
    DDL = """
    CREATE TABLE IF NOT EXISTS reg_items (
        id TEXT PRIMARY KEY,
        recorded_at TEXT NOT NULL,
        effective_date TEXT,
        category TEXT NOT NULL,
        region TEXT,
        title TEXT NOT NULL,
        summary_md TEXT NOT NULL,
        source_url TEXT,
        source_org TEXT,
        change_type TEXT NOT NULL,
        impact_notes TEXT,
        tags_csv TEXT
    );
    """
    with connect() as con:
        con.executescript(DDL)

require_login()
ensure_db()

# Sidebar
view = st.sidebar.radio("Ansicht", ["Radar", "Preise"], index=0)
st.sidebar.image(LOGO_PATH, width=120)
st.sidebar.markdown("### Filter")
days = st.sidebar.slider("Zeitraum (Tage)", 1, 90, DEFAULT_DAYS)
category = st.sidebar.multiselect("Kategorie", ["EEG","BEG","KfW","MSBG","Tarif","Netzentgelt","Sonstiges"])
region = st.sidebar.multiselect("Region", ["DE","BW","BY","BE","BB","HB","HH","HE","MV","NI","NW","RP","SL","SN","ST","SH","TH","EU"])
search = st.sidebar.text_input("Volltextsuche")

def query_items(days, category, region, search):
    conds, params = [], []
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).replace(microsecond=0).isoformat() + "Z"
    conds.append("recorded_at >= ?"); params.append(since)
    if category:
        conds.append("category IN ({})".format(",".join(["?"]*len(category)))); params.extend(category)
    if region:
        conds.append("(region IN ({}) OR (region IS NULL AND ? IN ('DE')))".format(",".join(["?"]*len(region))))
        params.extend(region)
        params.append("DE")
    if search:
        conds.append("(title LIKE ? OR summary_md LIKE ? OR impact_notes LIKE ? OR tags_csv LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like])
    q = "SELECT recorded_at, effective_date, category, region, title, summary_md, source_url, source_org, change_type, impact_notes, tags_csv FROM reg_items"
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY recorded_at DESC"
    with connect() as con:
        cur = con.execute(q, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        import pandas as pd
        df = pd.DataFrame(rows, columns=cols)
    return df

def render_pricing():
    st.image(LOGO_PATH, width=140)
    st.markdown("<div class='radar-title'>Preise & Lizenzen</div>", unsafe_allow_html=True)
    with open("config/tiers.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tiers = data.get("tiers", [])
    cols = st.columns(len(tiers)) if tiers else [st]
    for i, t in enumerate(tiers):
        with cols[i]:
            st.markdown(f"<div class='price-card'><div class='price-title'>{t['name']}</div>", unsafe_allow_html=True)
            money = f\"{t['price_eur_per_month']} € / Monat\"
            st.markdown(f"<div class='price-money'>{money}</div>", unsafe_allow_html=True)
            if t.get('includes_vat') is False:
                st.caption("zzgl. USt.")
            feats = t.get('features', [])
            st.markdown("<div class='price-feat'><ul>" + "".join([f"<li>{f}</li>" for f in feats]) + "</ul></div></div>", unsafe_allow_html=True)
    st.info("Hinweis: Preise für MVP/Frühbucher; Konditionen können je nach Umfang variieren.")

df = query_items(days, category, region, search)

if view == "Preise":
    render_pricing()
else:
    st.markdown(f"<div class='radar-title'>Änderungsradar · letzte {days} Tage</div>", unsafe_allow_html=True)
    st.caption("Hinweis: Kuratierte Informationen ohne Gewähr. Quellenangaben prüfen.")
    if df.empty:
        st.info("Keine Einträge im gewählten Zeitraum/Filter.")
    else:
        st.metric("Anzahl Einträge", len(df))
        st.dataframe(df, use_container_width=True)
        st.download_button("Export CSV", df.to_csv(index=False).encode("utf-8"), file_name="radar_export.csv", mime="text/csv")

        def render_md(df):
            lines = ["# Digest (Vorschau)", ""]
            last_cat = None
            last_reg = None
            for _, r in df.sort_values(["category","region","recorded_at"], ascending=[True,True,False]).iterrows():
                if r["category"] != last_cat:
                    lines.append(f"## {r['category']}"); last_cat = r["category"]; last_reg = None
                if r["region"] != last_reg:
                    lines.append(f"### Region: {r['region'] or 'DE (bundesweit)'}"); last_reg = r["region"]
                eff = f"(gültig ab {r['effective_date']})" if r["effective_date"] else ""
                src = f"[Quelle]({r['source_url']})" if r["source_url"] else (r["source_org"] or "Quelle n/a")
                lines.append(f"- **{r['title']}** {eff} — _{r['change_type']}_  \n  {r['summary_md']}  \n  {src}")
                if r["impact_notes"]:
                    lines.append(f"  \n  **Wirkung:** {r['impact_notes']}")
                if r["tags_csv"]:
                    lines.append(f"  \n  _Tags:_ {r['tags_csv']}")
                lines.append("")
            return "\n".join(lines)
        st.markdown(render_md(df))

    st.divider()
    st.markdown("**Rechtlicher Hinweis:** Die Inhalte sind nach bestem Wissen kuratiert, ersetzen jedoch keine Rechts- oder Steuerberatung. Keine Gewähr für Vollständigkeit oder Aktualität.")
