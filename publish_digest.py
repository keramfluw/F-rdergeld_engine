
#!/usr/bin/env python3
import os, sqlite3, datetime, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DB_PATH = os.environ.get("FT_RADAR_DB_PATH", "data/radar.db")
DAYS = int(os.environ.get("FT_RADAR_DIGEST_DAYS", "7"))
OUT_MD = os.environ.get("FT_RADAR_DIGEST_MD", "data/digest_last_7_days.md")
OUT_HTML = os.environ.get("FT_RADAR_DIGEST_HTML", "data/digest_last_7_days.html")

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
MAIL_FROM = os.environ.get("MAIL_FROM")
MAIL_TO = os.environ.get("MAIL_TO")  # comma-separated
MAIL_SUBJECT = os.environ.get("MAIL_SUBJECT", "Förder- & Tarif-Radar – Weekly Digest")

def connect():
    return sqlite3.connect(DB_PATH)

def fetch_items(days):
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).replace(microsecond=0).isoformat() + "Z"
    q = """SELECT recorded_at, effective_date, category, region, title, summary_md, source_url, source_org, change_type, impact_notes, tags_csv
           FROM reg_items WHERE recorded_at >= ? ORDER BY category, region, recorded_at DESC"""
    with connect() as con:
        return con.execute(q, (since,)).fetchall()

def render_md(rows):
    lines = ["# Förder- & Tarif-Radar – Digest (letzte {} Tage)".format(DAYS), ""]
    if not rows:
        lines.append("_Keine neuen Einträge im Zeitraum._")
        return "\\n".join(lines)
    last_cat = None
    last_region = None
    for r in rows:
        recorded_at, effective_date, category, region, title, summary_md, source_url, source_org, change_type, impact_notes, tags_csv = r
        if category != last_cat:
            lines.append(f"## {category}")
            last_cat = category
            last_region = None
        if region != last_region:
            lines.append(f"### Region: {region or 'DE (bundesweit)'}")
            last_region = region
        eff = f"(gültig ab {effective_date})" if effective_date else ""
        src = f"[Quelle]({source_url})" if source_url else (source_org or "Quelle n/a")
        lines.append(f"- **{title}** {eff} — _{change_type}_  \\n  {summary_md}  \\n  {src}")
        if impact_notes:
            lines.append(f"  \\n  **Wirkung:** {impact_notes}")
        if tags_csv:
            lines.append(f"  \\n  _Tags:_ {tags_csv}")
        lines.append("")
    return "\\n".join(lines)

def md_to_html(md_text):
    import html
    html_lines = []
    for line in md_text.splitlines():
        if line.startswith("# "):
            html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- **"):
            html_lines.append(f"<p>{line.replace('**','<b>').replace('**','</b>').replace('_','<i>').replace('_','</i>')}</p>")
        else:
            html_lines.append(f"<p>{line}</p>")
    return "\\n".join(html_lines)

def write_files(md_text, html_text):
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_text)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_text)

def send_email(html_text):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and MAIL_FROM and MAIL_TO):
        print("E-Mail-Versand übersprungen (SMTP-Variablen nicht vollständig).")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = MAIL_SUBJECT
    msg["From"] = MAIL_FROM
    msg["To"] = ",".join([x.strip() for x in MAIL_TO.split(",")])
    msg.attach(MIMEText(html_text, "html", "utf-8"))
    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    print("OK: Digest versendet.")

def main():
    rows = fetch_items(DAYS)
    md = render_md(rows)
    html = md_to_html(md)
    write_files(md, html)
    print(f"OK: Digest -> {OUT_MD}, {OUT_HTML}")
    send_email(html)

if __name__ == "__main__":
    main()
