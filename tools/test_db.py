import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env")

url = os.getenv("DATABASE_URL")
if not url:
    raise ValueError("DATABASE_URL IS NOT FOUND")

with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        print("database:", cur.fetchone()[0])

        cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """)
        print("tables:", [row[0] for row in cur.fetchall()])