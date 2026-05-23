# Contributing

Thank you for considering a contribution. This project exists to reduce confusion and friction for Muslim families in Singapore at the hardest moments. Accuracy and tone matter more than speed.

## Who should contribute

- Asatizah recognised under the Asatizah Recognition Scheme (ARS) in Singapore
- Doctors, nurses, palliative care professionals, and medical social workers
- Funeral directors and pengurus jenazah
- Syariah lawyers and inheritance specialists
- Community workers in mosques, MUIS, AMP, PERGAS, MENDAKI, AIC
- Family members who have recently navigated this and want to add what was missing

## Ways to contribute

1. Add or correct a corpus entry.
2. Add a primary source with URL and access date.
3. Translate Arabic or Malay terms in the glossary.
4. Add a sample question and walkthrough in `docs/examples/`.
5. Improve retrieval or chat scripts.
6. Flag scholarly disagreement that the companion handles too one-sidedly.

## Corpus file rules

Every markdown file in `corpus/` must have YAML front matter at the top:

```yaml
---
title: A short human-readable title
tags: [topic, subtopic]
summary: One or two sentences that describe what this file answers.
sources:
  - name: Source name
    url: https://example.gov.sg/...
    accessed: 2026-05-23
    note: One-line credibility statement.
---
```

Body rules:

- Plain calm English. Short paragraphs.
- No em dashes. Use commas or periods.
- Italicise Arabic and Malay terms on first use and add them to the glossary.
- Cite sources as numbered footnotes, like `[^1]`.
- Where qualified scholars disagree, present the mainstream Singapore-MUIS position first, briefly note other respected views, and recommend asatizah consultation.
- Do not paste large copyrighted material. Summarise and cite.
- Never include names of real people, hospital ward numbers, real ticket numbers, or personal medical details.

## Review workflow

1. Open a pull request with your change.
2. Tag at least one reviewer with relevant expertise where possible (asatizah for fiqh, doctor for medical framing, lawyer for inheritance).
3. The maintainer will run the test suite locally before merging.
4. For changes touching fiqh, the maintainer will seek asatizah review where possible. If you are an asatizah, please indicate your ARS status in the pull request description so it can be acknowledged in `docs/scholar-review.md`.

## Running tests locally

```bash
pip install -r rag/requirements.txt
python -m pytest -q
```

The retrieval test will skip if Ollama is not running. The corpus integrity test and the private-reference scrub test will always run.

## Code of conduct

Be kind. Be patient. Many readers are bereaved. Many contributors are volunteers.
