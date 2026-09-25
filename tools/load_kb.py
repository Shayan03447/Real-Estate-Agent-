import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, str(Path(__file__).parent))
from build_kb import split_sections, make_chunks, embed_texts


ROOT = Path(__file__).resolve().parent.parent
TENANT = "landmark"
SOURCE = "landmark-developers-clean.md"

def flags(heading: str) -> tuple[bool, bool]:
    historical = "Historical" in heading or "Pre-Launch" in heading
    claim = "claim" in heading or "Statement and Positioning" in heading
    return historical, claim

def main():
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL IS NOT FOUND")

    md_path = ROOT / "kb" / "landmark-developers-clean.md"
    sections = split_sections(md_path)
    chunks = [c for s in sections for c in make_chunks(s)]
    print(f"{len(sections)} sections -> {len(chunks)} chunks")

    print("embedding chunks....")
    vectors = embed_texts([c["content"] for c in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("vectors and chunks have different lengths")
    with psycopg.connect(url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kb_section Where tenant_id = %s", (TENANT,))
            print(f"deleted {cur.rowcount} sectrions")

            id_map = {}
            for s in sections:
                historical, claim = flags(s["heading"])
                cur.execute(
                    """
                    INSERT INTO kb_section
                        (tenant_id, source, heading_path, body,
                         is_historical, is_claim)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (TENANT, SOURCE, s["heading"], s["body"],
                     historical, claim),
                )
                db_id = cur.fetchone()[0]
                id_map[s["id"]] = db_id
            for chunk, vector in zip(chunks, vectors):
                cur.execute(
                    """
                    INSERT INTO kb_chunk
                        (section_id, tenant_id, content, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_map[chunk["section_id"]], TENANT,
                     chunk["content"], vector),
                )
        conn.commit()
    print(f"saved {len(id_map)} sections, {len(chunks)} chunks")
if __name__ == "__main__":
    main()
