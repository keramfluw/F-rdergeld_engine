
#!/usr/bin/env python3
import argparse, json, os, sqlite3, sys, datetime, uuid

DB_PATH = os.environ.get("FT_RADAR_DB_PATH", "data/radar.db")

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
CREATE INDEX IF NOT EXISTS idx_recorded_at ON reg_items(recorded_at);
CREATE INDEX IF NOT EXISTS idx_category ON reg_items(category);
CREATE INDEX IF NOT EXISTS idx_region ON reg_items(region);
"""

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as con:
        con.executescript(DDL)
    print(f"OK: Datenbank initialisiert @ {DB_PATH}")

def add_item(args):
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    rec = {
        "id": args.id or str(uuid.uuid4()),
        "recorded_at": now,
        "effective_date": args.effective_date,
        "category": args.category,
        "region": args.region,
        "title": args.title,
        "summary_md": args.summary_md,
        "source_url": args.source_url,
        "source_org": args.source_org,
        "change_type": args.change_type,
        "impact_notes": args.impact_notes,
        "tags_csv": args.tags_csv,
    }
    with connect() as con:
        con.execute("""
            INSERT INTO reg_items (id, recorded_at, effective_date, category, region, title, summary_md,
                                   source_url, source_org, change_type, impact_notes, tags_csv)
            VALUES (:id, :recorded_at, :effective_date, :category, :region, :title, :summary_md,
                    :source_url, :source_org, :change_type, :impact_notes, :tags_csv)
        """, rec)
        con.commit()
    print(f"OK: Eintrag gespeichert (id={rec['id']})")

def list_items(args):
    q = "SELECT id, recorded_at, effective_date, category, region, title, change_type FROM reg_items"
    conds, params = [], []
    if args.category:
        conds.append("category = ?"); params.append(args.category)
    if args.region:
        conds.append("region = ?"); params.append(args.region)
    if args.days:
        since = (datetime.datetime.utcnow() - datetime.timedelta(days=args.days)).replace(microsecond=0).isoformat() + "Z"
        conds.append("recorded_at >= ?"); params.append(since)
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY recorded_at DESC LIMIT ?"
    params.append(args.limit)
    with connect() as con:
        cur = con.execute(q, params)
        rows = cur.fetchall()
        for r in rows:
            print("| ".join(str(x) if x is not None else "-" for x in r))

def import_json(args):
    with open(args.path, "r", encoding="utf-8") as f:
        items = json.load(f)
    with connect() as con:
        for it in items:
            con.execute("""
                INSERT OR REPLACE INTO reg_items (id, recorded_at, effective_date, category, region, title, summary_md,
                                   source_url, source_org, change_type, impact_notes, tags_csv)
                VALUES (:id, :recorded_at, :effective_date, :category, :region, :title, :summary_md,
                        :source_url, :source_org, :change_type, :impact_notes, :tags_csv)
            """, it)
        con.commit()
    print(f"OK: {len(items)} Einträge importiert")

def export_json(args):
    q = "SELECT * FROM reg_items ORDER BY recorded_at DESC"
    with connect() as con:
        cur = con.execute(q)
        cols = [d[0] for d in cur.description]
        out = [dict(zip(cols, r)) for r in cur.fetchall()]
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(out)} Einträge exportiert -> {args.path}")

def parse_args():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init-db")

    p_add = sub.add_parser("add")
    p_add.add_argument("--id", default=None)
    p_add.add_argument("--effective_date", default=None)
    p_add.add_argument("--category", required=True)
    p_add.add_argument("--region", default=None)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--summary_md", required=True)
    p_add.add_argument("--source_url", default=None)
    p_add.add_argument("--source_org", default=None)
    p_add.add_argument("--change_type", required=True, choices=["Neu","Änderung","Auslaufend","Klarstellung"])
    p_add.add_argument("--impact_notes", default=None)
    p_add.add_argument("--tags_csv", default=None)

    p_list = sub.add_parser("list")
    p_list.add_argument("--category")
    p_list.add_argument("--region")
    p_list.add_argument("--days", type=int)
    p_list.add_argument("--limit", type=int, default=50)

    p_imp = sub.add_parser("import-json")
    p_imp.add_argument("path")

    p_exp = sub.add_parser("export-json")
    p_exp.add_argument("path")

    return p.parse_args()

def main():
    args = parse_args()
    if args.cmd == "init-db":
        init_db()
    elif args.cmd == "add":
        add_item(args)
    elif args.cmd == "list":
        list_items(args)
    elif args.cmd == "import-json":
        import_json(args)
    elif args.cmd == "export-json":
        export_json(args)
    else:
        print("Unbekannter Befehl", file=sys.stderr); sys.exit(2)

if __name__ == "__main__":
    main()
