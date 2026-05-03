"""KDoc IDP — Streamlit demo UI.

The UI is the *sales surface*: a prospect drops a PDF in and within seconds sees
the structured Markdown, table CSVs, RAG chunks (with page citations), and
quality warnings — the four things every IDP buyer asks for in the first demo.
"""

from __future__ import annotations

import io
import json
import os

import httpx
import streamlit as st

API_URL = os.getenv("UI_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="KDoc IDP", layout="wide")
st.title("KDoc IDP — Document → LLM-ready Data")
st.caption(
    "Drop a PDF / DOCX / image in. Get clean Markdown, structured tables, and "
    "RAG-ready chunks with page citations. Self-hosted via Docling — no docs leave your machine."
)


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=600.0)


with st.sidebar:
    st.header("Try it")
    uploaded = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "pptx", "xlsx", "html", "md", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )
    include_rag = st.checkbox("Include RAG-ready chunks", value=True)
    run = st.button("Extract", type="primary", disabled=uploaded is None)

    st.divider()
    if st.button("Load demo extraction (no install needed)"):
        with _client() as c:
            resp = c.get("/api/demo")
            resp.raise_for_status()
            st.session_state["result"] = resp.json()
            st.session_state["source"] = "demo"

    st.divider()
    st.caption("API: `POST /api/extract` · `POST /api/jobs` · `GET /api/jobs/{id}`")


if run and uploaded is not None:
    with st.spinner(f"Extracting {uploaded.name}..."):
        with _client() as c:
            files = {
                "file": (
                    uploaded.name,
                    uploaded.getvalue(),
                    uploaded.type or "application/octet-stream",
                )
            }
            resp = c.post("/api/extract", files=files, params={"rag": str(include_rag).lower()})
            if resp.status_code == 503:
                st.warning(resp.json().get("detail", "extraction unavailable"))
            else:
                resp.raise_for_status()
                st.session_state["result"] = resp.json()
                st.session_state["source"] = uploaded.name

result = st.session_state.get("result")
if not result:
    st.info("Upload a file or click **Load demo extraction** in the sidebar to begin.")
    st.stop()

# ---------------- Top-line metrics ----------------
metrics = st.columns(4)
metrics[0].metric("Pages", result.get("page_count", 0))
metrics[1].metric("Sections", len(result.get("sections", [])))
metrics[2].metric("Tables", len(result.get("tables", [])))
extractor = result.get("extractor", {})
metrics[3].metric(
    "Engine",
    extractor.get("engine", "—"),
    delta=f"{extractor.get('elapsed_ms', 0)} ms" if extractor.get("elapsed_ms") else None,
)

if extractor.get("note"):
    st.warning(extractor["note"])

# ---------------- Quality signals (front and center) ----------------
warnings = result.get("warnings", [])
if warnings:
    severity_color = {"info": "blue", "warning": "orange", "error": "red"}
    with st.expander(
        f"Quality signals ({len(warnings)})",
        expanded=any(w["severity"] != "info" for w in warnings),
    ):
        for w in warnings:
            color = severity_color.get(w["severity"], "gray")
            st.markdown(f":{color}[**[{w['severity']}] {w['code']}**] — {w['message']}")
            if w.get("suggestion"):
                st.caption(f"→ {w['suggestion']}")

# ---------------- Tabs ----------------
tabs = st.tabs(["Markdown", "Tables", "RAG Chunks", "Sections", "Raw JSON"])

with tabs[0]:
    md = result.get("markdown", "")
    st.download_button(
        "Download Markdown",
        data=md.encode("utf-8"),
        file_name=f"{result.get('source_name', 'extraction')}.md",
        mime="text/markdown",
    )
    st.markdown(md or "_(empty)_")

with tabs[1]:
    tables = result.get("tables", [])
    if not tables:
        st.info("No tables detected. (This is expected for prose-only documents.)")
    for t in tables:
        st.subheader(f"Table #{t['index']} — page {t['page'] or '?'} · {t['n_rows']}×{t['n_cols']}")
        if t.get("caption"):
            st.caption(t["caption"])
        rows = t["rows"]
        if rows:
            # Render the first row as header for visual clarity even if has_header is uncertain.
            st.dataframe(rows[1:] if t.get("has_header") and len(rows) > 1 else rows)
            csv_bytes = io.StringIO()
            import csv as _csv

            _csv.writer(csv_bytes).writerows(rows)
            st.download_button(
                f"Download table {t['index']:02d} as CSV",
                data=csv_bytes.getvalue().encode("utf-8"),
                file_name=f"table-{t['index']:02d}-p{t['page'] or 0:03d}.csv",
                mime="text/csv",
                key=f"dl-{t['index']}",
            )

with tabs[2]:
    chunks = result.get("rag_chunks") or []
    if not chunks:
        st.info("RAG chunks were not requested.")
    else:
        st.write(f"**{len(chunks)} chunks** ready for embedding / vector ingest.")
        jsonl = "\n".join(
            json.dumps(
                {
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    "metadata": {
                        "source_name": result.get("source_name"),
                        "heading_path": c["heading_path"],
                        "page_start": c["page_start"],
                        "page_end": c["page_end"],
                        "token_estimate": c["token_estimate"],
                    },
                },
                ensure_ascii=False,
            )
            for c in chunks
        )
        st.download_button(
            "Download chunks as JSONL",
            data=jsonl.encode("utf-8"),
            file_name=f"{result.get('source_name', 'extraction')}.chunks.jsonl",
            mime="application/x-ndjson",
        )
        for c in chunks[:30]:
            path = " > ".join(c["heading_path"]) or "(unsectioned)"
            page_label = (
                f"p.{c['page_start']}-{c['page_end']}"
                if c["page_start"] != c["page_end"]
                else f"p.{c['page_start']}"
            )
            st.markdown(f"**{path}** · {page_label} · ~{c['token_estimate']} tokens")
            st.code(c["text"], language="markdown")
        if len(chunks) > 30:
            st.caption(f"…and {len(chunks) - 30} more (download JSONL for the full set).")

with tabs[3]:
    sections = result.get("sections", [])
    for s in sections:
        path = " > ".join(s["heading_path"]) or "(unsectioned)"
        page_label = (
            f"p.{s['page_start']}-{s['page_end']}"
            if s["page_start"] != s["page_end"]
            else f"p.{s['page_start']}"
        )
        st.markdown(f"**{path}** · level {s['level']} · {page_label}")
        st.write(s["text"])
        st.divider()

with tabs[4]:
    st.json(result)
