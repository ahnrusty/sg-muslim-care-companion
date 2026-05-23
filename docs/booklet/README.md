# Booklet

The bereavement booklet is a single PDF compiled from the entire corpus, formatted for an A5 pocket-friendly print.

## Where the latest PDF lives

- Versioned, committed copy: [`docs/booklet/sg-muslim-care-companion-booklet.pdf`](./sg-muslim-care-companion-booklet.pdf). Linked from the top-level README's "Download the booklet" section. Suitable for direct download from GitHub by non-technical users.
- Local build output: `dist/sg-muslim-care-companion-booklet.pdf` (gitignored).

### Why an in-repo copy

The committed PDF is around 0.4 to 0.8 MB at A5, well under the 2 MB threshold mentioned in the v2 brief, so Git LFS is not needed and a GitHub Actions workflow is not strictly required. The committed copy ships with each tag so a non-technical user can download the booklet directly from the GitHub UI without running any tooling.

If the booklet grows past 2 MB in future, switch to either:

1. Git LFS for the file, or
2. A GitHub Actions release workflow that builds the PDF and attaches it as a release asset.

Either approach is straightforward; the build script is fully reproducible.

## How to build it locally

```bash
cd sg-muslim-care-companion
python3 -m venv .venv
source .venv/bin/activate
pip install -r rag/requirements.txt
pip install -r requirements-pdf.txt
python scripts/export_pdf.py
```

This writes `dist/sg-muslim-care-companion-booklet.pdf`.

To override the version label on the cover:

```bash
python scripts/export_pdf.py --version v0.2.1
```

## What is in the booklet

- Cover with title, subtitle, version, "Community Edition", and the full disclaimer.
- Table of contents with page numbers.
- All corpus content except machine-readable `mosques.json`, `contacts.json`, and the 70 per-mosque markdown files (those are best read via `python rag/directory.py`, not as a 70-page block of repeated contact pages).
- Footnotes carry through with their bracketed numbers; readers can cross-reference each source from the per-section sources blocks.
- Page numbers in the footer; section names in the running footer.
- A5 page size, Helvetica 10pt body, 14pt leading.

## Pure-Python toolchain

The script uses [ReportLab](https://www.reportlab.com/opensource/) (pinned in `requirements-pdf.txt`). No Cairo or Pango. Works on macOS and Linux out of the box.
