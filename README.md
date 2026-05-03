# KDoc IDP

> **Self-hosted Intelligent Document Processing — turn messy enterprise documents into LLM-ready Markdown, JSON, and tables. No docs leave your machine.**

Built around [Docling](https://github.com/DS4SD/docling) (IBM, MIT licensed), exposed as a FastAPI service with a Streamlit demo UI.

---

## Why this exists — four pain points we hear every week

| Pain | What customers do today | What KDoc IDP does |
|---|---|---|
| **"Tables come out garbled."** RAG answers wrong because the model lost merged cells / column alignment. | Manual cleanup, or ditch table-heavy docs from the corpus. | Docling's TableFormer model is the differentiator. We surface every table with a confidence panel and one-click CSV export so you can verify before ingest. |
| **"I can't send sensitive contracts to AWS / Azure / Google."** Legal, healthcare, finance, and government workloads either can't legally use cloud OCR or dread the audit. | Stay on Adobe desktop or in-house Tesseract — both painful. | 100% self-hosted. Pure Python, runs on your laptop or a single Linux box. No outbound calls, no usage telemetry. |
| **"My RAG hallucinates and I can't audit it."** No way to point users back to the source page. | Hand-roll page tracking on top of `pdfplumber`. | Every `RagChunk` carries `page_start` / `page_end` and the heading path. Citation comes free. |
| **"Mixed formats break my pipeline."** PDF, DOCX, XLSX, scanned images, HTML emails — five different libraries, five different bugs. | Stitch together `pdfminer` + `python-docx` + `openpyxl` + `pytesseract`. | One adapter (Docling) covers PDF, DOCX, PPTX, XLSX, HTML, Markdown, PNG, JPEG. One output schema. |

---

## Who it's for

- **KDAN PDF Reader / DottedSign**: feed extracted form fields and tables into signing workflows; auto-suggest signer slots from contract structure.
- **Legal / Compliance teams** (Taiwan PDPA · EU GDPR · CCPA): contract clause extraction, vendor-risk audits, redaction prep — all on-prem.
- **RAG / GenAI builders**: drop-in replacement for Unstructured.io / LlamaParse when data residency matters.
- **Document-heavy SMBs** (clinics, accounting firms, gov agencies): batch-process reports without per-page cloud fees.

> ⚠️ **Compliance reminder.** KDAN operates under Taiwan PDPA, GDPR, and CCPA. Contract-related and PII-bearing extractions: please verify with KDAN's legal or compliance team before finalizing.

---

## Comparison

| | KDoc IDP (Docling) | Adobe PDF Extract | AWS Textract | Unstructured.io |
|---|---|---|---|---|
| Self-host / on-prem | ✅ | ❌ | ❌ | ⚠️ Paid tier |
| Table-structure model | ✅ TableFormer | ✅ | ✅ | ⚠️ Heuristic |
| Heading-aware sections | ✅ | ⚠️ | ❌ | ✅ |
| Page citations in output | ✅ | ⚠️ | ⚠️ | ✅ |
| Per-page cost | $0 (compute) | ~$0.05 | ~$0.0015–$0.05 | ~$0.01 |
| Data leaves your network | ❌ | ✅ | ✅ | ✅ Hosted |
| License | MIT | Commercial | Commercial | Apache 2 + commercial |

Numbers are public list pricing as of 2026-Q1; verify before quoting externally.

---

## Architecture

```
app/
├── core/
│   ├── types.py            # ExtractedDocument / Section / Table / RagChunk / QualitySignal
│   ├── docling_runner.py   # Lazy Docling adapter (DocumentConverter → ExtractedDocument)
│   ├── quality.py          # Heuristic warnings: scanned-only, sparse table, flat structure...
│   ├── chunker.py          # Heading-aware RAG chunker, propagates page citations
│   └── exports.py          # markdown · full JSON · CSV per table · RAG JSONL
├── services/
│   ├── pipeline.py         # bytes → ExtractedDocument (or demo fixture if Docling missing)
│   ├── jobs.py             # in-memory async job store (swap to Redis/Celery in prod)
│   └── demo_fixture.py     # pre-baked extraction so the UI demos with zero install
├── api/v1/routes/
│   ├── extract.py          # POST /api/extract (sync) · POST /api/jobs (async)
│   ├── jobs.py             # GET /api/jobs · GET /api/jobs/{id}
│   ├── tables.py           # GET /api/jobs/{id}/tables/{idx}.csv
│   └── demo.py             # GET /api/demo  (works without Docling)
└── web/streamlit_app.py    # drag-drop UI, tabs, downloads, quality panel
```

Internal types live in `app/core/types.py`. **Nothing outside `docling_runner.py` imports `docling`** — that's how the API and tests stay green when the heavy extra isn't installed.

---

## Install

The base install is light (FastAPI + Streamlit + Pydantic), so CI / demos start in seconds:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

To enable real extraction (downloads PyTorch + IBM layout / table models on first run):

```bash
pip install -e '.[extract]'
```

If `[extract]` is not installed, the service runs in **demo mode** — it returns a realistic pre-baked extraction so you can preview the UI and integrate with the API contract before committing to the full install.

---

## Run

Terminal A — API:

```bash
API_PORT=8204 ./scripts/dev_api.sh
```

Terminal B — UI:

```bash
UI_API_URL=http://127.0.0.1:8204 streamlit run app/web/streamlit_app.py --server.port 8604
```

Open <http://127.0.0.1:8604>, drop in a PDF, or click **Load demo extraction** in the sidebar.

---

## API

```bash
# Health
curl -s http://127.0.0.1:8204/api/health

# Demo (no install required)
curl -s http://127.0.0.1:8204/api/demo | jq '.tables[0]'

# Sync extract — returns the full ExtractedDocument + RAG chunks
curl -s -X POST http://127.0.0.1:8204/api/extract \
     -F file=@report.pdf -F rag=true | jq

# Async — submit, poll, download a table
JOB=$(curl -s -X POST http://127.0.0.1:8204/api/jobs -F file=@report.pdf | jq -r .job_id)
curl -s http://127.0.0.1:8204/api/jobs/$JOB | jq .status
curl -s http://127.0.0.1:8204/api/jobs/$JOB/tables/0.csv -o table-0.csv
```

### Response shape (the contract a downstream RAG / DB ingest depends on)

```jsonc
{
  "source_name": "report.pdf",
  "page_count": 12,
  "extractor": {"engine": "docling", "elapsed_ms": 4230, "options": {...}},
  "warnings": [{"code": "sparse_table", "severity": "warning", "message": "...", "suggestion": "..."}],
  "sections": [{"heading": "...", "level": 2, "heading_path": ["Doc", "Intro"], "text": "...", "page_start": 1, "page_end": 1}],
  "tables":   [{"index": 0, "page": 4, "n_rows": 5, "n_cols": 5, "rows": [["Region", "Vendors", ...], ...]}],
  "markdown": "# Report\n\n...",
  "rag_chunks": [{"chunk_id": "...", "text": "...", "heading_path": [...], "page_start": 4, "page_end": 4, "token_estimate": 412}]
}
```

---

## Tests

```bash
PYTHONPATH=. python3 -m pytest      # 23 tests, no Docling required
./scripts/fmt_lint.sh               # ruff format + check
```

The CI path uses demo mode — heavy extraction is exercised manually with `.[extract]` installed.

---

## Roadmap to GTM

What this repo *is*: a working technical foundation + the marketing-ready story.
What it *isn't yet* (and what shipping requires):

- [ ] **Hardened deployment** — Dockerfile, single-binary install, health/readiness probes
- [ ] **Auth + multi-tenancy** — API keys, per-tenant quotas, audit log
- [ ] **Side-by-side preview** — render the original page next to the extracted Markdown for QA (needs `pdf2image` + page thumbnails)
- [ ] **Batch UI** — drop a folder, get a zip of artifacts
- [ ] **Swap out the in-memory job store** for Redis/Celery; add retry + dead-letter
- [ ] **Adapters for KDAN PDF Reader & DottedSign** — extracted form fields → signer slots; extracted tables → fillable form templates
- [ ] **Pricing & licensing** — tiers (Open Source / Self-Host / Managed) and trial flow
- [ ] **Beachhead customer** — pick one of the personas above and build the integration end-to-end

---

## License

MIT (matches Docling). KDAN-internal usage and external pilots both fine.

*Pricing, partnerships, and external deployment plans require review by the relevant KDAN team lead before external use.*
