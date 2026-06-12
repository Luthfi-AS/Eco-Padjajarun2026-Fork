"""Export every table in db.sqlite3 to its own CSV file in csv_export/.

Usage:
    python export_csv.py

Pure standard library (sqlite3 + csv) — no extra dependencies needed.
"""

import csv
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "db.sqlite3"
OUT = BASE / "csv_export"


def main():
    if not DB.exists():
        raise SystemExit(f"Database not found: {DB}")

    OUT.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    tables = [
        row[0]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]

    for table in tables:
        rows = cur.execute(f'SELECT * FROM "{table}"').fetchall()
        cols = [desc[0] for desc in cur.description]

        with open(OUT / f"{table}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)

        print(f"{table}: {len(rows)} rows")

    conn.close()
    print(f"\nDone. {len(tables)} tables exported to {OUT}")


if __name__ == "__main__":
    main()
