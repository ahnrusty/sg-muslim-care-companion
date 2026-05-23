"""Compile corpus/ into a single A5 printable bereavement booklet PDF.

Uses ReportLab so the toolchain is pure Python (no Cairo/Pango). Produces:

  dist/sg-muslim-care-companion-booklet.pdf

Run:

  pip install -r requirements-pdf.txt
  python scripts/export_pdf.py

Optional flags:

  --out PATH      Override output path.
  --version STR   Override the version string printed on the cover.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS = REPO_ROOT / "corpus"
DEFAULT_OUT = REPO_ROOT / "dist" / "sg-muslim-care-companion-booklet.pdf"

# Order of sections (matches the corpus directory ordering plus the directory subtree).
SECTION_ORDER: list[tuple[str, str]] = [
    ("Overview", "00-overview.md"),
    ("Critical illness", "10-critical-illness"),
    ("Imminent death", "20-imminent-death"),
    ("Fardhu kifayah", "30-fardhu-kifayah"),
    ("Singapore admin", "40-singapore-admin"),
    ("After burial", "50-after-burial"),
    ("Inheritance", "60-inheritance"),
    ("Financial and community", "70-financial-and-community"),
    ("Directory", "80-directory"),
    ("Glossary", "90-glossary"),
]

# Files / directory subtrees to skip from the booklet (machine-readable artifacts).
SKIP_NAMES = {"mosques.json", "contacts.json"}
SKIP_DIRS = {"mosques"}  # 70 mosque entries would balloon the booklet


# ---------------------------------------------------------------------------
# Markdown loader
# ---------------------------------------------------------------------------


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[3:end].strip()) or {}
    body = text[end + 4 :].lstrip("\n")
    return fm, body


def section_files(section_path: Path) -> list[Path]:
    if section_path.is_file():
        return [section_path]
    files: list[Path] = []
    for entry in sorted(section_path.iterdir()):
        if entry.is_dir():
            if entry.name in SKIP_DIRS:
                continue
            files.extend(section_files(entry))
        elif entry.is_file() and entry.suffix == ".md" and entry.name not in SKIP_NAMES:
            files.append(entry)
    return files


# ---------------------------------------------------------------------------
# Minimal Markdown to ReportLab flowables
# ---------------------------------------------------------------------------


INLINE_RE = re.compile(
    r"(\*\*(?P<bold>[^*]+)\*\*"
    r"|\*(?P<em>[^*]+)\*"
    r"|`(?P<code>[^`]+)`"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)"
    r"|\[\^(?P<fn>[^\]]+)\])"
)


def md_inline_to_xml(text: str) -> str:
    """Convert a single Markdown line into ReportLab paragraph XML."""

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    out: list[str] = []
    i = 0
    for m in INLINE_RE.finditer(text):
        out.append(esc(text[i : m.start()]))
        if m.group("bold"):
            out.append(f"<b>{esc(m.group('bold'))}</b>")
        elif m.group("em"):
            out.append(f"<i>{esc(m.group('em'))}</i>")
        elif m.group("code"):
            out.append(f'<font name="Courier">{esc(m.group("code"))}</font>')
        elif m.group("link_text"):
            url = esc(m.group("link_url"))
            label = esc(m.group("link_text"))
            out.append(f'<link href="{url}"><u>{label}</u></link>')
        elif m.group("fn"):
            out.append(f'<super>[{esc(m.group("fn"))}]</super>')
        i = m.end()
    out.append(esc(text[i:]))
    return "".join(out)


def md_blocks(body: str) -> Iterable[tuple[str, str, int]]:
    """Yield (kind, text, level) blocks from a Markdown body."""
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("###### "):
            yield "h", line[7:].strip(), 6
            i += 1
            continue
        if line.startswith("##### "):
            yield "h", line[6:].strip(), 5
            i += 1
            continue
        if line.startswith("#### "):
            yield "h", line[5:].strip(), 4
            i += 1
            continue
        if line.startswith("### "):
            yield "h", line[4:].strip(), 3
            i += 1
            continue
        if line.startswith("## "):
            yield "h", line[3:].strip(), 2
            i += 1
            continue
        if line.startswith("# "):
            yield "h", line[2:].strip(), 1
            i += 1
            continue
        if line.startswith("> "):
            block = [line[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                block.append(lines[i][2:])
                i += 1
            yield "blockquote", "\n".join(block).strip(), 0
            continue
        if line.startswith("- ") or line.startswith("* "):
            items: list[str] = []
            while i < len(lines) and (
                lines[i].startswith("- ") or lines[i].startswith("* ")
            ):
                items.append(lines[i][2:].strip())
                i += 1
            yield "list", "\n".join(items), 0
            continue
        if re.match(r"^\d+\.\s", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i] or ""):
                items.append(re.sub(r"^\d+\.\s", "", lines[i]).strip())
                i += 1
            yield "olist", "\n".join(items), 0
            continue
        if (
            line.startswith("|")
            and i + 1 < len(lines)
            and re.match(r"^\|\s*[:\-]+", lines[i + 1])
        ):
            tbl: list[str] = [line]
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                tbl.append(lines[i])
                i += 1
            yield "table", "\n".join(tbl), 0
            continue
        if line.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            yield "code", "\n".join(block), 0
            continue
        if re.match(r"^\[\^[^\]]+\]:", line):
            yield "footnote_def", line, 0
            i += 1
            continue
        block = [line]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not lines[i].startswith(("#", "- ", "* ", ">", "|", "```"))
            and not re.match(r"^\d+\.\s", lines[i])
        ):
            block.append(lines[i])
            i += 1
        yield "p", " ".join(block), 0


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------


def build_pdf(out_path: Path, version: str) -> None:
    try:
        from reportlab.lib.pagesizes import A5
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            PageBreak,
            Table,
            TableStyle,
        )
    except ImportError:
        print(
            "reportlab not installed. Run: pip install -r requirements-pdf.txt",
            file=sys.stderr,
        )
        sys.exit(2)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceBefore=0,
        spaceAfter=3,
        allowOrphans=1,
        allowWidows=1,
    )
    h1_style = ParagraphStyle(
        "H1",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=0,
        textColor=colors.HexColor("#222222"),
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        spaceBefore=6,
        spaceAfter=4,
        keepWithNext=0,
        textColor=colors.HexColor("#333333"),
    )
    h3_style = ParagraphStyle(
        "H3",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=0,
        textColor=colors.HexColor("#444444"),
    )
    quote_style = ParagraphStyle(
        "Quote",
        parent=body_style,
        leftIndent=10,
        rightIndent=10,
        textColor=colors.HexColor("#555555"),
        backColor=colors.HexColor("#F4F4F4"),
        borderPadding=4,
    )
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=1,
    )
    cover_sub_style = ParagraphStyle(
        "CoverSub",
        parent=body_style,
        fontSize=13,
        leading=17,
        alignment=1,
        spaceBefore=8,
    )
    cover_meta_style = ParagraphStyle(
        "CoverMeta",
        parent=body_style,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#666666"),
    )
    toc_style = ParagraphStyle(
        "TOC",
        parent=body_style,
        fontSize=10,
        leading=15,
        leftIndent=0,
    )
    code_style = ParagraphStyle(
        "Code",
        parent=body_style,
        fontName="Courier",
        fontSize=9,
        leading=12,
        leftIndent=10,
        textColor=colors.HexColor("#222222"),
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=1,
        spaceBefore=12,
        spaceAfter=16,
        keepWithNext=0,
        textColor=colors.HexColor("#222222"),
    )

    # Use A5 portrait. Margins kept generous for readability on a small page.
    page_w, page_h = A5
    margin = 12 * mm
    footer_h = 10 * mm

    current_section = {"name": "Cover"}

    def draw_chrome(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(margin, 10 * mm, f"SG Muslim Care Companion {version}")
        canvas.drawRightString(page_w - margin, 10 * mm, f"Page {doc.page}")
        canvas.drawCentredString(page_w / 2, 6 * mm, current_section["name"])
        canvas.restoreState()

    story: list = []

    # ---- Cover ----
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("SG Muslim Care Companion", cover_title_style))
    story.append(
        Paragraph(
            "A local-first guide for Muslim families in Singapore navigating critical "
            "illness, end-of-life, and bereavement.",
            cover_sub_style,
        )
    )
    story.append(Spacer(1, 20 * mm))
    today = dt.date.today().isoformat()
    story.append(
        Paragraph(
            f"Community Edition &middot; {version} &middot; {today}", cover_meta_style
        )
    )
    story.append(Spacer(1, 30 * mm))
    disclaimer_text = (
        "<b>Disclaimer.</b> This booklet is a community-benefit navigator. It is not "
        "a substitute for a qualified asatizah (ARS-certified in Singapore), a "
        "licensed medical professional, or a Syariah lawyer. Religious rulings "
        "should be confirmed with the Office of the Mufti or your local mosque "
        "imam. Medical decisions must be made with the treating doctor. Legal and "
        "inheritance decisions should involve the Syariah Court of Singapore or a "
        "qualified Muslim lawyer."
    )
    story.append(Paragraph(disclaimer_text, body_style))
    story.append(PageBreak())

    # ---- Table of contents (page numbers filled in below by ReportLab built-in is overkill;
    # we instead enumerate sections and resolve page numbers via a TOCEntry list.) ----
    story.append(Paragraph("Table of Contents", h1_style))
    story.append(Spacer(1, 4 * mm))
    toc_placeholder_index = len(story)
    story.append(Paragraph("(Generated on render)", toc_style))
    story.append(PageBreak())

    # Track sections to build TOC.
    toc_entries: list[tuple[str, int]] = []

    def add_section(name: str, files: list[Path]):
        current_section_name = name
        toc_entries.append((current_section_name, -1))  # placeholder for page number
        # Always start sections on a new page to keep layout predictable.
        story.append(Paragraph(current_section_name, section_header_style))
        story.append(Spacer(1, 2 * mm))

        for f in files:
            raw = f.read_text(encoding="utf-8")
            fm, body = parse_front_matter(raw)
            title = fm.get("title") or f.stem
            story.append(Paragraph(title, h1_style))
            story.append(Spacer(1, 1 * mm))
            for kind, text, level in md_blocks(body):
                if kind == "h":
                    style = {1: h1_style, 2: h2_style, 3: h3_style}.get(level, h3_style)
                    story.append(Paragraph(md_inline_to_xml(text), style))
                elif kind == "p":
                    story.append(Paragraph(md_inline_to_xml(text), body_style))
                elif kind == "blockquote":
                    for para in text.split("\n\n"):
                        story.append(Paragraph(md_inline_to_xml(para), quote_style))
                elif kind == "list":
                    for it in text.split("\n"):
                        if it.strip():
                            story.append(
                                Paragraph(
                                    "&bull; " + md_inline_to_xml(it.strip()),
                                    body_style,
                                )
                            )
                elif kind == "olist":
                    for n, it in enumerate(text.split("\n"), 1):
                        if it.strip():
                            story.append(
                                Paragraph(
                                    f"{n}. " + md_inline_to_xml(it.strip()),
                                    body_style,
                                )
                            )
                elif kind == "table":
                    rows = []
                    for ln in text.split("\n"):
                        if re.match(r"^\|\s*[:\-]+", ln):
                            continue
                        cells = [c.strip() for c in ln.strip("|").split("|")]
                        rows.append(
                            [Paragraph(md_inline_to_xml(c), body_style) for c in cells]
                        )
                    if rows:
                        tbl = Table(rows, hAlign="LEFT", repeatRows=1)
                        tbl.setStyle(
                            TableStyle(
                                [
                                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
                                    (
                                        "BACKGROUND",
                                        (0, 0),
                                        (-1, 0),
                                        colors.HexColor("#EEEEEE"),
                                    ),
                                    (
                                        "LINEBELOW",
                                        (0, 0),
                                        (-1, 0),
                                        0.5,
                                        colors.HexColor("#888888"),
                                    ),
                                    (
                                        "GRID",
                                        (0, 0),
                                        (-1, -1),
                                        0.25,
                                        colors.HexColor("#CCCCCC"),
                                    ),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ]
                            )
                        )
                        story.append(tbl)
                elif kind == "code":
                    story.append(Paragraph(text.replace("\n", "<br/>"), code_style))
                elif kind == "footnote_def":
                    story.append(Paragraph(md_inline_to_xml(text), body_style))
            story.append(Spacer(1, 4 * mm))

        story.append(PageBreak())

    # Walk sections
    for section_name, path in SECTION_ORDER:
        p = CORPUS / path
        if not p.exists():
            continue
        files = section_files(p)
        if not files:
            continue
        add_section(section_name, files)

    # Closing page
    story.append(Paragraph("End of booklet", h1_style))
    story.append(
        Paragraph(
            "This is the end of the SG Muslim Care Companion booklet. "
            "Updates and the latest version are at "
            '<link href="https://github.com/ahnrusty/sg-muslim-care-companion">'
            "github.com/ahnrusty/sg-muslim-care-companion</link>.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "May Allah ease the path for every family that picks this up.",
            body_style,
        )
    )

    section_pages: dict[str, int] = {}

    # Monkey-patch handle_flowable to silently page-break instead of raising
    # LayoutError when a small flowable would otherwise fail. Some versions
    # of ReportLab raise even when allowSplitting=1 if a paragraph happens to
    # wrap exactly at the frame boundary; we recover by issuing a page break
    # and retrying.
    from reportlab.platypus import doctemplate as _dt
    from reportlab.platypus.doctemplate import LayoutError as _LE

    _orig_handle = _dt.BaseDocTemplate.handle_flowable

    def _patched_handle(self, flowables):
        try:
            return _orig_handle(self, flowables)
        except _LE:
            if not flowables:
                return
            f = flowables[0]
            self.handle_pageBreak()
            return _orig_handle(self, flowables)

    _dt.BaseDocTemplate.handle_flowable = _patched_handle

    def make_doc(path: Path) -> "SimpleDocTemplate":
        return SimpleDocTemplate(
            str(path),
            pagesize=A5,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin + footer_h,
            title="SG Muslim Care Companion",
            author="ahnrusty",
            allowSplitting=1,
        )

    import copy

    first_pass_path = out_path.with_suffix(".pass1.pdf")
    first_doc = make_doc(first_pass_path)

    def first_after(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "SectionHeader":
            section_pages[flowable.getPlainText()] = self.page
            current_section["name"] = flowable.getPlainText()

    first_doc.afterFlowable = first_after.__get__(first_doc)
    first_story = copy.copy(story)
    first_doc.build(first_story, onFirstPage=draw_chrome, onLaterPages=draw_chrome)
    first_pass_path.unlink(missing_ok=True)

    if toc_entries:
        toc_paras = [
            Paragraph(
                f'{name}<font color="#888888"> ........... </font>'
                f"{section_pages.get(name, '?')}",
                toc_style,
            )
            for name, _ in toc_entries
        ]
        story[toc_placeholder_index : toc_placeholder_index + 1] = toc_paras
    else:
        story[toc_placeholder_index] = Paragraph("(no sections)", toc_style)

    current_section["name"] = "Cover"
    final_doc = make_doc(out_path)

    def final_after(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "SectionHeader":
            current_section["name"] = flowable.getPlainText()

    final_doc.afterFlowable = final_after.__get__(final_doc)
    final_doc.build(story, onFirstPage=draw_chrome, onLaterPages=draw_chrome)

    print(f"Wrote {out_path} ({out_path.stat().st_size / 1024:.0f} KiB)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile corpus into an A5 PDF booklet."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--version", default="v0.2.0")
    args = parser.parse_args()
    build_pdf(args.out, args.version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
