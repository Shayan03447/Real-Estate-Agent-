from pathlib import Path
import re
from pathlib import Path

SEP_CELL = re.compile(r":?-{2,}:?$")
MIN_CHARS = 20



def split_sections(md_path: Path) -> list[dict]:
    lines = md_path.read_text(encoding ="utf-8").splitlines()
    doc  = lines[0].lstrip("# ").strip()

    out = []
    h2 = ""
    heading = doc
    buf = []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            out.append({"id": len(out) + 1, "heading": heading, "body": body})

    for line in lines[1:]:
        if line.startswith("## "):
            flush()
            h2 = line.lstrip("# ").strip()
            heading, buf = f"{doc} > {h2}", []
        elif line.startswith("### "):
            flush()
            heading, buf = f"{doc} > {h2} > {line.lstrip('# ').strip()}", []
        else:
            buf.append(line)
        
    flush()
    return out 


def clean(lines: list[str]) -> str:
    out = []
    for line in lines:
        lines = re.sub(r"\*\*|`", "", line)
        line = re.sub(r"^[>#*-]+\s+", "", line.strip())
        if line:
            out.append(line)
    return re.sub(r"\s+", " ", " ".join(out)).strip()

if __name__ == "__main__":
    for s in split_sections(Path("kb/landmark-developers-clean.md")):
        print(f"id={s['id']:<3} {len(s['body']):>5} chars {s['heading']}")


def ends_with_colon(line: str) -> bool:
    return line.rstrip().rstrip("*").endswith(":")

def attach_notes(blocks):
    out = []
    for block in blocks:
        kind, payload, _ = block
        if kind == "prose" and payload[0].startswith(">") and out and out[-1][0] == "prose":
            out[-1][1].extend(payload)
            continue
        out.append(block)
    return out

def split_blocks(body: str):
    blocks, buf, table = [], [], []
    label = ""

    def flush_prose():
        if buf:
            blocks.append(["prose", list(buf), ""])
            buf.clear()

    def flush_table():
        nonlocal label
        if table:
            blocks.append(["table", list(table), label])
            table.clear()
            label = ""

    for raw in body.splitlines():
        line= raw.strip()

        if line.startswith("|"):
            if not table nad buf and ends_with_colon(buf[-1]):
                label = buf.pop()
            flush_prose()
            table.append(line)
            continue
        flush_table()

        if not line or line == "---":
            if buf and not ends_with_colon(buf[-1]):
                flush_prose()
            continue

        buf.append(line)
    
    flush_prose()
    flush_table()
    return attach_notes(blocks)
