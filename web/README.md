# KDoc IDP — Web (Next.js)

The customer-facing demo / sales surface. Talks to the FastAPI backend at
`/api/extract` and `/api/demo`.

## Dev

```bash
cd web
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if not localhost:8000
npm install
npm run dev                        # http://localhost:3000
```

Make sure the backend is running too:

```bash
# In another terminal, from the repo root:
API_PORT=8000 ./scripts/dev_api.sh
```

## Build

```bash
npm run build
npm start
```

## Layout

```
web/
├── src/
│   ├── app/
│   │   ├── layout.tsx        Root layout
│   │   ├── page.tsx          Single page: drop-zone → side-by-side result
│   │   └── globals.css
│   ├── components/
│   │   ├── DropZone.tsx
│   │   ├── PdfViewer.tsx     react-pdf, exposes scrollToPage()
│   │   ├── ExtractionPanel.tsx  Tabs orchestrator
│   │   ├── MarkdownPanel.tsx
│   │   ├── TablesPanel.tsx
│   │   ├── ChunksPanel.tsx   RAG chunks w/ jump-to-page
│   │   ├── SectionsPanel.tsx
│   │   ├── QualityPanel.tsx
│   │   └── Header.tsx
│   └── lib/
│       ├── api.ts            Typed fetch wrapper
│       └── types.ts          Mirror of app/core/types.py
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
└── next.config.mjs
```

## Why Next.js (and not just Streamlit)

Streamlit is great for internal data-team users; this app is the **sales surface** —
the side-by-side PDF preview with click-to-jump page citations is the wedge feature
buyers ask for in the first demo. PDF.js + canvas is unsuitable for Streamlit, so
the two roles split:

- **`app/web/streamlit_app.py`** → internal QA / dev iteration
- **`web/`** (this directory) → external demo / GTM / embedding into KDAN
  PDF Reader & DottedSign

Both talk to the same FastAPI backend.
