# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to semantic versioning where practical.

## [v0.2.0] -- 2026-05-23

### Added

- **PDF bereavement booklet export.** `scripts/export_pdf.py` compiles the entire corpus into a single A5 printable PDF using ReportLab (pure Python toolchain). The committed copy lives at `docs/booklet/sg-muslim-care-companion-booklet.pdf`; the local build output is `dist/sg-muslim-care-companion-booklet.pdf` (gitignored). New `requirements-pdf.txt` pins the toolchain. See [`docs/booklet/README.md`](docs/booklet/README.md).
- **MUIS mosque directory.** New corpus subtree `corpus/80-directory/mosques/` with one markdown file per mosque (70 files), plus a flat machine-readable index at `corpus/80-directory/mosques.json`. Sourced from `muis.gov.sg` mosque directory pages, every entry cites its MUIS source URL. Where the MUIS individual page is unavailable, the entry is marked `unknown -- verify with mosque directly`.
- **Consolidated contact list.** `corpus/80-directory/contacts.md` and `corpus/80-directory/contacts.json` cover emergency lines, MUIS, burial booking and cemetery contacts, death registration, public hospital general enquiries, caregiving and community support, mental health, Syariah Court and inheritance, Muslim funeral providers, and legal help. Every entry is sourced from a public URL.
- **Directory CLI.** `rag/directory.py` with `--list`, `--mosque <name>`, `--postal <code>`, and `--contacts`. Postal-code lookup is best-effort by postal-code prefix, fully local.
- **Syariah Court Inheritance Certificate walkthrough.** Interactive CLI at `rag/walkthroughs/inheritance_certificate.py`. Builds a tailored documents and steps checklist from short yes/no questions. Triggerable inside `python rag/chat.py` with `/walkthrough inheritance-cert`. The corpus file `corpus/60-inheritance/syariah-court-inheritance-certificate.md` is expanded into a step-by-step walkthrough covering documents, fees, timeline, overseas and minor beneficiaries, how the IC is used at banks / CPF / HDB / insurance / brokers, and common rejection reasons.
- **Tests.** `tests/test_directory_integrity.py` validates the JSON schemas and per-mosque markdown. Golden retrieval cases added for "How do I apply for a Syariah inheritance certificate?", "Phone number for Pusara Aman mosque?", and "Where is Masjid Sultan?".

### Changed

- `tests/test_corpus_integrity.py` now skips the per-mosque subtree, which is covered by `test_directory_integrity.py` with a leaner schema.
- `README.md` adds "Download the booklet", "Walkthroughs", and "Directory and contacts" sections.

### Notes

- Temenggong mosque: the MUIS individual mosque page returned 404 at the time of writing, so its directory entry is marked as needing direct verification. All 69 other mosques have full MUIS-sourced address and phone data.

## [v0.1.0] -- 2026-05-23

### Added

- Initial release. 35 corpus files, 157 citations, RAG implementation on local Ollama (`nomic-embed-text` + `gemma3:e4b`), tests, privacy scrub, and skill / rules files for Cursor / Claude Code / Copilot / Amp.
