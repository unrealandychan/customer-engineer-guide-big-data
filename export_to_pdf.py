#!/usr/bin/env python3
"""
export_to_pdf.py
----------------
Converts every .md file in the project-g repo to a styled PDF.
Uses only pure-Python libraries — no Homebrew, no system C libraries needed.

Usage:
    python3 export_to_pdf.py                       # all files → ./pdf-export/
    python3 export_to_pdf.py --out ~/Desktop/pdfs  # custom output dir
    python3 export_to_pdf.py --file docs/00-guideline.md  # single file

Requirements (install once):
    pip3 install --user markdown reportlab
"""

import argparse
import html
import re
import sys
from pathlib import Path

# ── Colours & sizes ──────────────────────────────────────────────────────────
C_INDIGO   = (0.31, 0.27, 0.90)   # headings accent / table header bg
C_NAVY     = (0.12, 0.23, 0.37)   # h2 colour
C_DARK     = (0.12, 0.14, 0.17)   # body text
C_MID      = (0.25, 0.33, 0.43)   # blockquote text
C_LIGHT    = (0.96, 0.97, 0.98)   # even-row table bg
C_CODE_BG  = (0.95, 0.95, 0.97)   # inline code bg
C_PRE_BG   = (0.12, 0.16, 0.24)   # fenced code block bg
C_PRE_FG   = (0.88, 0.91, 0.95)   # fenced code text
C_HR       = (0.90, 0.91, 0.93)   # horizontal rule
C_WHITE    = (1, 1, 1)
C_BLUE_LT  = (0.94, 0.97, 1.0)    # blockquote background

PAGE_W, PAGE_H = 595, 842          # A4 points
ML, MR, MT, MB = 54, 54, 60, 54   # margins
TW = PAGE_W - ML - MR              # text width


# ── Markdown → token stream ───────────────────────────────────────────────────

def tokenize(md: str) -> list[dict]:
    """
    Very lightweight Markdown tokenizer → list of block tokens.
    Supports: headings, fenced code, blockquotes, tables, hr, bullet/numbered
    lists, and paragraphs (with inline bold/italic/code/strikethrough).
    """
    tokens: list[dict] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            tokens.append({"type": "code", "lang": lang, "text": "\n".join(code_lines)})
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line):
            tokens.append({"type": "hr"})
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            tokens.append({"type": "heading", "level": len(m.group(1)), "text": m.group(2).strip()})
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            bq_lines = []
            while i < len(lines) and lines[i].startswith(">"):
                bq_lines.append(lines[i].lstrip("> ").rstrip())
                i += 1
            tokens.append({"type": "blockquote", "text": " ".join(bq_lines)})
            continue

        # Table (pipe-separated, GitHub flavour)
        if "|" in line and i + 1 < len(lines) and re.match(r"^\|?[-:| ]+\|", lines[i + 1]):
            rows = []
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(header)
            i += 2  # skip separator row
            while i < len(lines) and "|" in lines[i]:
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(row)
                i += 1
            tokens.append({"type": "table", "rows": rows})
            continue

        # Bullet list
        if re.match(r"^(\s*)([-*+]|\d+\.)\s+", line):
            items = []
            while i < len(lines) and re.match(r"^(\s*)([-*+]|\d+\.)\s+", lines[i]):
                m2 = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)", lines[i])
                indent = len(m2.group(1)) // 2
                ordered = bool(re.match(r"\d+\.", m2.group(2)))
                items.append({"text": m2.group(3), "indent": indent, "ordered": ordered})
                i += 1
            tokens.append({"type": "list", "items": items})
            continue

        # Blank line
        if line.strip() == "":
            i += 1
            continue

        # Paragraph (accumulate until blank or block element)
        para_lines = []
        while i < len(lines):
            l = lines[i]
            if l.strip() == "":
                break
            if re.match(r"^#{1,4}\s|^[-*_]{3,}\s*$|^\s*[-*+]\s|^\s*\d+\.\s|^>|^\|.*\||^```", l):
                break
            para_lines.append(l.strip())
            i += 1
        if para_lines:
            tokens.append({"type": "para", "text": " ".join(para_lines)})

    return tokens


# ── Inline rendering ──────────────────────────────────────────────────────────

def inline_text(raw: str) -> list[tuple[str, str]]:
    """
    Parse inline Markdown and return list of (text, style) tuples.
    Styles: 'normal', 'bold', 'italic', 'bold_italic', 'code'
    Strips emoji for PDF safety (reportlab built-in font doesn't support them).
    """
    # Remove emoji / symbols outside Latin + common Unicode
    raw = re.sub(r"[^\x00-\x7F\u00C0-\u024F\u2010-\u2027\u2030-\u206F]", "", raw)
    # Strip markdown link syntax → keep label text
    raw = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", raw)
    # Strip bare URLs
    raw = re.sub(r"https?://\S+", "", raw)

    result = []
    pattern = re.compile(
        r"(\*\*\*(.+?)\*\*\*"      # bold+italic
        r"|\*\*(.+?)\*\*"           # bold
        r"|__(.+?)__"               # bold alt
        r"|\*(.+?)\*"               # italic
        r"|_(.+?)_"                 # italic alt
        r"|`([^`]+)`"               # inline code
        r"|~~(.+?)~~)",             # strikethrough → normal
        re.DOTALL,
    )
    last = 0
    for m in pattern.finditer(raw):
        if m.start() > last:
            result.append((raw[last:m.start()], "normal"))
        if m.group(2):
            result.append((m.group(2), "bold_italic"))
        elif m.group(3) or m.group(4):
            result.append((m.group(3) or m.group(4), "bold"))
        elif m.group(5) or m.group(6):
            result.append((m.group(5) or m.group(6), "italic"))
        elif m.group(7):
            result.append((m.group(7), "code"))
        elif m.group(8):
            result.append((m.group(8), "normal"))
        last = m.end()
    if last < len(raw):
        result.append((raw[last:], "normal"))
    return result or [("", "normal")]


# ── PDF renderer ──────────────────────────────────────────────────────────────

def md_to_pdf(md_path: Path, out_dir: Path) -> Path:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader

    text = md_path.read_text(encoding="utf-8")
    tokens = tokenize(text)

    try:
        rel = md_path.relative_to(ROOT)
    except ValueError:
        rel = Path(md_path.name)

    pdf_path = out_dir / rel.with_suffix(".pdf")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    c.setTitle(md_path.stem.replace("-", " ").replace("_", " ").title())
    c.setAuthor("GCP Interview Prep")

    # ── font helpers ──
    def font(bold=False, italic=False, mono=False):
        if mono:
            return "Courier"
        if bold and italic:
            return "Helvetica-BoldOblique"
        if bold:
            return "Helvetica-Bold"
        if italic:
            return "Helvetica-Oblique"
        return "Helvetica"

    STYLE_FONT = {
        "normal":      ("Helvetica",              9.5),
        "bold":        ("Helvetica-Bold",          9.5),
        "italic":      ("Helvetica-Oblique",       9.5),
        "bold_italic": ("Helvetica-BoldOblique",   9.5),
        "code":        ("Courier",                 8.5),
    }

    y = PAGE_H - MT
    page_num = [1]

    def new_page():
        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawRightString(PAGE_W - MR, 30, str(page_num[0]))
        c.drawString(ML, 30, md_path.stem)
        page_num[0] += 1
        c.showPage()
        return PAGE_H - MT

    def check_space(needed, cur_y):
        if cur_y - needed < MB:
            return new_page()
        return cur_y

    # ── inline word-wrap paragraph ──
    def draw_para(spans, cur_y, left=ML, width=TW, line_h=13, first_indent=0):
        """Draw wrapped inline text. Returns new y."""
        words = []
        for (txt, style) in spans:
            fn, fs = STYLE_FONT[style]
            # split on spaces but keep them attached to the prior word
            for word in txt.split(" "):
                if word:
                    words.append((word + " ", style, fn, fs))

        x = left + first_indent
        line_words: list[tuple] = []
        line_w = 0.0

        def flush_line(lwords, lx, ly):
            cx = lx
            for (w, sty, fn2, fs2) in lwords:
                c.setFont(fn2, fs2)
                if sty == "code":
                    # light bg pill
                    tw2 = c.stringWidth(w.rstrip(), fn2, fs2)
                    c.setFillColorRGB(*C_CODE_BG)
                    c.rect(cx - 1, ly - 2, tw2 + 2, fs2 + 2, fill=1, stroke=0)
                c.setFillColorRGB(*C_DARK)
                c.drawString(cx, ly, w)
                cx += c.stringWidth(w, fn2, fs2)
            return ly - line_h

        for (w, sty, fn2, fs2) in words:
            ww = c.stringWidth(w, fn2, fs2)
            if x + line_w + ww > left + width and line_words:
                cur_y = check_space(line_h, cur_y)
                flush_line(line_words, left + first_indent if x == left + first_indent else left, cur_y)
                cur_y -= line_h
                line_words = [(w, sty, fn2, fs2)]
                line_w = ww
                x = left
            else:
                line_words.append((w, sty, fn2, fs2))
                line_w += ww

        if line_words:
            cur_y = check_space(line_h, cur_y)
            flush_line(line_words, left, cur_y)
            cur_y -= line_h

        return cur_y

    # ── render tokens ──
    for tok in tokens:
        t = tok["type"]

        # --- Heading ---
        if t == "heading":
            lvl = tok["level"]
            raw = re.sub(r"[^\x00-\x7F\u00C0-\u024F]", "", tok["text"])
            raw = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", raw)
            if lvl == 1:
                y = check_space(40, y)
                y -= 6
                c.setFont("Helvetica-Bold", 18)
                c.setFillColorRGB(*C_DARK)
                c.drawString(ML, y, raw)
                y -= 4
                c.setStrokeColorRGB(*C_INDIGO)
                c.setLineWidth(2.5)
                c.line(ML, y, ML + TW, y)
                y -= 12
            elif lvl == 2:
                y = check_space(32, y)
                y -= 14
                c.setFont("Helvetica-Bold", 13)
                c.setFillColorRGB(*C_NAVY)
                c.drawString(ML, y, raw)
                y -= 3
                c.setStrokeColorRGB(*C_HR)
                c.setLineWidth(1)
                c.line(ML, y, ML + TW, y)
                y -= 8
            elif lvl == 3:
                y = check_space(24, y)
                y -= 10
                c.setFont("Helvetica-Bold", 11)
                c.setFillColorRGB(0.22, 0.27, 0.34)
                c.drawString(ML, y, raw)
                y -= 8
            else:
                y = check_space(18, y)
                y -= 8
                c.setFont("Helvetica-BoldOblique", 9.5)
                c.setFillColorRGB(*C_INDIGO)
                c.drawString(ML, y, raw)
                y -= 6

        # --- Horizontal rule ---
        elif t == "hr":
            y = check_space(16, y)
            y -= 8
            c.setStrokeColorRGB(*C_HR)
            c.setLineWidth(1.2)
            c.line(ML, y, ML + TW, y)
            y -= 8

        # --- Fenced code block ---
        elif t == "code":
            code_lines = tok["text"].splitlines()
            line_h = 11
            block_h = len(code_lines) * line_h + 16
            y = check_space(min(block_h, PAGE_H - MT - MB), y)
            y -= 6
            c.setFillColorRGB(*C_PRE_BG)
            c.rect(ML, y - block_h + line_h, TW, block_h, fill=1, stroke=0)
            # left accent bar
            c.setFillColorRGB(*C_INDIGO)
            c.rect(ML, y - block_h + line_h, 3, block_h, fill=1, stroke=0)
            cy = y - 4
            c.setFont("Courier", 7.5)
            c.setFillColorRGB(*C_PRE_FG)
            for cl in code_lines:
                if cy - line_h < MB:
                    y = new_page()
                    cy = y - 4
                    c.setFillColorRGB(*C_PRE_BG)
                    c.rect(ML, cy - (len(code_lines) * line_h), TW, len(code_lines) * line_h + 8, fill=1, stroke=0)
                    c.setFont("Courier", 7.5)
                    c.setFillColorRGB(*C_PRE_FG)
                # strip non-latin for Courier safety
                cl_safe = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", cl)
                c.drawString(ML + 8, cy, cl_safe[:110])
                cy -= line_h
            y = cy - 6

        # --- Blockquote ---
        elif t == "blockquote":
            spans = inline_text(tok["text"])
            y = check_space(30, y)
            y -= 4
            # measure height
            c.setFillColorRGB(*C_BLUE_LT)
            c.rect(ML, y - 30, TW, 36, fill=1, stroke=0)
            c.setFillColorRGB(0.23, 0.51, 0.95)
            c.rect(ML, y - 30, 3, 36, fill=1, stroke=0)
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColorRGB(*C_MID)
            y = draw_para(spans, y - 4, left=ML + 10, width=TW - 14, line_h=12)
            y -= 6

        # --- Table ---
        elif t == "table":
            rows = tok["rows"]
            if not rows:
                continue
            cols = max(len(r) for r in rows)
            col_w = TW / cols
            row_h = 16
            table_h = len(rows) * row_h
            y = check_space(min(table_h + 10, PAGE_H - MT - MB), y)
            y -= 6
            for ri, row in enumerate(rows):
                if y - row_h < MB:
                    y = new_page()
                if ri == 0:
                    # header
                    c.setFillColorRGB(*C_INDIGO)
                    c.rect(ML, y - row_h + 4, TW, row_h, fill=1, stroke=0)
                    c.setFont("Helvetica-Bold", 8)
                    c.setFillColorRGB(*C_WHITE)
                elif ri % 2 == 0:
                    c.setFillColorRGB(*C_LIGHT)
                    c.rect(ML, y - row_h + 4, TW, row_h, fill=1, stroke=0)
                    c.setFont("Helvetica", 8)
                    c.setFillColorRGB(*C_DARK)
                else:
                    c.setFillColorRGB(*C_WHITE)
                    c.rect(ML, y - row_h + 4, TW, row_h, fill=1, stroke=0)
                    c.setFont("Helvetica", 8)
                    c.setFillColorRGB(*C_DARK)
                for ci, cell in enumerate(row):
                    cell_safe = re.sub(r"[^\x00-\x7F]", "", cell)
                    cell_safe = re.sub(r"\*+|`|_+|~~", "", cell_safe)  # strip markdown
                    x_cell = ML + ci * col_w + 3
                    # truncate if too wide
                    max_chars = int(col_w / 4.2)
                    if len(cell_safe) > max_chars:
                        cell_safe = cell_safe[:max_chars - 1] + "…"
                    c.drawString(x_cell, y - 8, cell_safe)
                # row bottom border
                c.setStrokeColorRGB(*C_HR)
                c.setLineWidth(0.3)
                c.line(ML, y - row_h + 4, ML + TW, y - row_h + 4)
                y -= row_h
            y -= 6

        # --- List ---
        elif t == "list":
            for idx, item in enumerate(tok["items"]):
                indent = item["indent"]
                ordered = item["ordered"]
                left = ML + 12 + indent * 16
                y = check_space(14, y)
                # bullet / number
                c.setFont("Helvetica-Bold", 9)
                c.setFillColorRGB(*C_INDIGO)
                bullet = f"{idx + 1}." if ordered else "•"
                c.drawString(left - 10, y, bullet)
                spans = inline_text(item["text"])
                y = draw_para(spans, y, left=left, width=TW - (left - ML) - 4, line_h=12)
            y -= 4

        # --- Paragraph ---
        elif t == "para":
            spans = inline_text(tok["text"])
            y = check_space(14, y)
            y = draw_para(spans, y, line_h=13)
            y -= 4

    # final footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawRightString(PAGE_W - MR, 30, str(page_num[0]))
    c.drawString(ML, 30, md_path.stem)
    c.save()
    return pdf_path


# ── File discovery ────────────────────────────────────────────────────────────

def collect_md_files(root: Path) -> list[Path]:
    skip_dirs = {".git", "node_modules", ".venv", "__pycache__", "pdf-export"}
    files = []
    for p in sorted(root.rglob("*.md")):
        if any(part in skip_dirs for part in p.parts):
            continue
        files.append(p)
    return files


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert all Markdown files in project-g to styled PDFs (no system dependencies)."
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "pdf-export",
        help="Output directory (default: ./pdf-export/)",
    )
    parser.add_argument(
        "--file", type=Path, default=None,
        help="Convert a single .md file instead of the whole repo",
    )
    args = parser.parse_args()

    out_dir: Path = args.out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [args.file.resolve()] if args.file else collect_md_files(ROOT)

    if not files:
        print("No .md files found.")
        sys.exit(0)

    print(f"  Found {len(files)} Markdown file(s)")
    print(f"  Output -> {out_dir}\n")

    ok, failed = [], []
    for i, md_file in enumerate(files, 1):
        try:
            rel_display = md_file.relative_to(ROOT)
        except ValueError:
            rel_display = md_file
        print(f"[{i:02d}/{len(files)}] {rel_display} ...", end=" ", flush=True)
        try:
            pdf = md_to_pdf(md_file, out_dir)
            size_kb = pdf.stat().st_size // 1024
            print(f"OK  ({size_kb} KB)")
            ok.append(pdf)
        except Exception as e:
            print(f"FAIL  {e}")
            failed.append((md_file, e))

    print(f"\n{'─' * 55}")
    print(f"  {len(ok)} converted  |  {len(failed)} failed")
    if failed:
        print("\nFailed:")
        for f, e in failed:
            print(f"  - {f.name}: {e}")
    print(f"\n  PDFs saved to: {out_dir}")


ROOT = Path(__file__).parent.resolve()

if __name__ == "__main__":
    main()
