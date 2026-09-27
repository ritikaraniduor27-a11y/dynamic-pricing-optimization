"""
Phase 2 — SQL Runner
Loads the Phase 1 synthetic dataset into SQLite and executes the analytical
queries in phase2_queries.sql, printing results for inspection.
"""

import sqlite3
import pandas as pd
import re

DB_PATH = "dynamic_pricing.db"
CSV_PATH = "dynamic_pricing_synthetic_data.csv"
SQL_FILE = "phase2_queries.sql"

# ---------------------------------------------------------------------
# 1. Load CSV into SQLite table `hourly_ops`
# ---------------------------------------------------------------------
df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
df["is_weekend"] = df["is_weekend"].astype(int)
df["payout_below_floor_flag"] = df["payout_below_floor_flag"].astype(int)

conn = sqlite3.connect(DB_PATH)
df.to_sql("hourly_ops", conn, if_exists="replace", index=False)

print(f"Loaded {len(df):,} rows into SQLite table `hourly_ops`.\n")

# ---------------------------------------------------------------------
# 2. Parse individual queries out of the .sql file (split on ';')
# ---------------------------------------------------------------------
with open(SQL_FILE, "r") as f:
    raw_sql = f.read()

# Split into statements, keep only non-empty SELECTs, capture preceding comment as title
blocks = re.split(r"\n(?=-- --)", raw_sql)
queries = []
for block in blocks:
    lines = block.strip().splitlines()
    title_lines = [l.replace("--", "").strip() for l in lines if l.strip().startswith("--")]
    title = " ".join([t for t in title_lines if t and "----" not in t][:2])
    sql_body = "\n".join([l for l in lines if not l.strip().startswith("--")]).strip()
    if sql_body:
        queries.append((title, sql_body.rstrip(";")))

# ---------------------------------------------------------------------
# 3. Execute each query and display results
# ---------------------------------------------------------------------
pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)

for i, (title, sql) in enumerate(queries, start=1):
    print("=" * 90)
    print(f"Q{i}: {title}")
    print("=" * 90)
    try:
        result = pd.read_sql_query(sql, conn)
        print(result.head(12).to_string(index=False))
    except Exception as e:
        print(f"ERROR running query: {e}")
    print()

conn.close()
