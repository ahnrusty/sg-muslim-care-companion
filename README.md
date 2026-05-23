# SG Muslim Care Companion

**Version: v0.2.0**

A local-first AI companion for Muslim families in Singapore navigating critical illness, end-of-life, and bereavement.

This is a community-benefit, anonymous open source project. It is built for the moments when a family is exhausted, grieving, and trying to figure out what to do next in a hospital corridor, at a bedside, or at a mosque office. It will not replace your asatizah, your doctor, or your Syariah lawyer. It will help you ask the right questions and find the right people, faster.

## What it covers

1. Critical illness and ICU situations, including the Islamic perspective on DNR, withdrawal of treatment, brain death, and organ donation.
2. The imminent moment of death and the first hour after, including talqin and bedside duties.
3. Fardhu kifayah, including ghusl, kafan, solat jenazah, and burial within 24 hours in Singapore.
4. Singapore administrative steps, including the Certificate of Cause of Death, ICA death registration, MUIS burial booking, and Muslim funeral service providers.
5. After burial commemorations, iddah, condolences, and grief support.
6. Wasiat, faraid, the Syariah Court Inheritance Certificate, hibah, nuzriah, and asset distribution under Muslim law in Singapore.
7. Financial and community support, including MUIS, AMP, PERGAS, MENDAKI, mosque zakat assistance, AIC, and bereavement leave norms.

## How it works

The companion uses a small local knowledge base of markdown files in `corpus/`. A retrieval layer pulls the most relevant chunks for each question and asks a local large language model to answer using only that context, with citations.

By default it runs entirely on your laptop using [Ollama](https://ollama.com). No data leaves your machine.

If you prefer, you can point it at any OpenAI-compatible endpoint by setting `OPENAI_BASE_URL` and `OPENAI_API_KEY`.

## Download the booklet

A printable bereavement booklet compiled from the entire corpus is available as a single A5 PDF.

- Download from the repo: [`docs/booklet/sg-muslim-care-companion-booklet.pdf`](docs/booklet/sg-muslim-care-companion-booklet.pdf)
- Build it locally: `pip install -r requirements-pdf.txt && python scripts/export_pdf.py`
- See [`docs/booklet/README.md`](docs/booklet/README.md) for details.

## Walkthroughs

Interactive process walkthroughs help you build a tailored checklist for common bereavement tasks.

| Walkthrough | Command | What it covers |
|-------------|---------|----------------|
| `inheritance-cert` | `python rag/walkthroughs/inheritance_certificate.py` or `/walkthrough inheritance-cert` inside `python rag/chat.py` | Syariah Court Inheritance Certificate documents, fees, timeline, overseas and minor beneficiaries. |
| `burial-booking` | (planned) | NEA Permit to Bury and Choa Chu Kang slot booking. |
| `wasiat-drafting` | (planned) | Wasiat preparation under AMLA. |

## Directory and contacts

- `python rag/directory.py --list` to list all MUIS mosques.
- `python rag/directory.py --mosque "Sultan"` to look up a mosque by name or slug.
- `python rag/directory.py --postal 198833` for a best-effort postal-code-prefix lookup.
- `python rag/directory.py --contacts` for the consolidated bereavement contact list.

Machine-readable copies: [`corpus/80-directory/mosques.json`](corpus/80-directory/mosques.json) and [`corpus/80-directory/contacts.json`](corpus/80-directory/contacts.json).

## Quick start

Prerequisites: macOS or Linux, Python 3.10+, [Ollama](https://ollama.com) installed and running on `localhost:11434`.

```bash
git clone https://github.com/ahnrusty/sg-muslim-care-companion.git
cd sg-muslim-care-companion
./scripts/setup.sh
python rag/chat.py
```

This will:

1. Pull the small chat model (`gemma3:e4b`, around 5 GB) and embedding model (`nomic-embed-text`).
2. Install Python dependencies from `rag/requirements.txt`.
3. Build the embedding index from `corpus/`.
4. Drop you into a chat prompt.

To ask a single question without a chat session:

```bash
python rag/query.py "What do I do in the first hour after my father passes away at the hospital?"
```

## Disclaimer

This project is a community-benefit navigator. It is not a substitute for a qualified asatizah (ARS-certified in Singapore), a licensed medical professional, or a Syariah lawyer. Religious rulings should be confirmed with the [Office of the Mufti](https://www.muis.gov.sg/officeofthemufti) or your local mosque imam. Medical decisions must be made with the treating doctor. Legal and inheritance decisions should involve the [Syariah Court of Singapore](https://www.syariahcourt.gov.sg) or a qualified Muslim lawyer.

See [DISCLAIMER.md](DISCLAIMER.md) for the full statement.

## Where the content comes from

Every corpus file lists its sources. We prioritise primary sources on `.gov.sg`, `muis.gov.sg`, mosque websites, MUIS publications, the Syariah Court, ICA, NEA, AIC, AMP, MENDAKI, PERGAS, and reputable academic or OIC Fiqh Academy sources for cross-Islamic context.

See [docs/corpus-sources.md](docs/corpus-sources.md) for the full source list with access dates.

## Voice and tone

Plain, calm, simple English. Short paragraphs. Where there is scholarly disagreement, the mainstream Singapore-MUIS position is presented first and other respected views are noted briefly, with a recommendation to consult an asatizah.

## Repo layout

```
corpus/              the knowledge base, version controlled markdown
rag/                 retrieval and chat scripts
skill/               agent skill, compatible with Cursor and Claude Code
rules/               system prompt and tool-agnostic agent rules
scripts/             setup, refresh, and pre-push scrubber
tests/               corpus integrity, retrieval, privacy checks
docs/                architecture notes, design rationale, source list
```

## Contributing

This project welcomes pull requests, particularly from asatizah, doctors, nurses, social workers, funeral directors, and community organisers in Singapore who can review and improve the corpus.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the review workflow.

## License

- Code: MIT, see [LICENSE](LICENSE).
- Corpus: CC BY 4.0. You may reuse and adapt the corpus, with attribution.

## Acknowledgement

Built quietly by one Singaporean Muslim during a difficult week, so the next family has one less thing to figure out alone.
