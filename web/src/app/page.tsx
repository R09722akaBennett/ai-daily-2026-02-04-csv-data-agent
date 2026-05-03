"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";

import { DropZone } from "@/components/DropZone";
import { ExtractionPanel } from "@/components/ExtractionPanel";
import { Header } from "@/components/Header";
import type { PdfViewerHandle } from "@/components/PdfViewer";
import { ApiError, extractFile, loadDemo } from "@/lib/api";
import type { ExtractedDocumentJson } from "@/lib/types";

// react-pdf hits `window` / canvas APIs — must be client-side only.
const PdfViewer = dynamic(() => import("@/components/PdfViewer").then((m) => m.PdfViewer), {
  ssr: false,
  loading: () => <div className="p-4 text-sm text-ink-400">Loading PDF viewer…</div>,
});

export default function Home() {
  const [doc, setDoc] = useState<ExtractedDocumentJson | null>(null);
  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pdfRef = useRef<PdfViewerHandle>(null);

  // Free the blob URL when we move on to a new file or unmount.
  useEffect(() => {
    if (!pdfBlob) return;
    return () => {
      // Object URLs are freed by GC; we explicitly hold the Blob, no URL to revoke here.
    };
  }, [pdfBlob]);

  async function handleFile(file: File) {
    setError(null);
    setLoading(true);
    setDoc(null);
    setPdfBlob(file.type.includes("pdf") || file.name.toLowerCase().endsWith(".pdf") ? file : null);
    try {
      const result = await extractFile(file, { rag: true });
      setDoc(result);
    } catch (e) {
      if (e instanceof ApiError) setError(e.detail);
      else setError(e instanceof Error ? e.message : String(e));
      setPdfBlob(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleDemo() {
    setError(null);
    setLoading(true);
    setDoc(null);
    setPdfBlob(null);
    try {
      setDoc(await loadDemo());
    } catch (e) {
      if (e instanceof ApiError) setError(e.detail);
      else setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setDoc(null);
    setPdfBlob(null);
    setError(null);
  }

  // ---------- Initial state ----------
  if (!doc && !loading) {
    return (
      <div className="flex min-h-full flex-col">
        <Header />
        <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-stretch justify-center gap-6 px-6 py-12">
          <div>
            <h2 className="text-2xl font-semibold text-ink-900">
              Document → LLM-ready data, in one click.
            </h2>
            <p className="mt-2 text-sm text-ink-600">
              Drop a PDF, DOCX, PPTX, XLSX, HTML, or image. Get clean Markdown, structured tables,
              and RAG-ready chunks with page citations. No file leaves your network — Docling runs
              entirely on your local FastAPI backend.
            </p>
          </div>
          <DropZone onFile={handleFile} />
          <div className="flex items-center justify-center gap-3 text-sm">
            <span className="text-ink-400">No PDF handy?</span>
            <button
              onClick={handleDemo}
              className="rounded-md border border-ink-200 bg-white px-3 py-1.5 text-ink-800 hover:bg-ink-50"
            >
              Load demo extraction
            </button>
          </div>
          {error ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
              {error}
            </div>
          ) : null}
          <ul className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
            <li className="rounded-lg border border-ink-200 bg-white p-3">
              <div className="font-medium text-ink-800">Tables that survive</div>
              <div className="mt-1 text-ink-600">
                Docling&apos;s TableFormer model preserves merged cells. Each table previewed inline,
                downloadable as CSV.
              </div>
            </li>
            <li className="rounded-lg border border-ink-200 bg-white p-3">
              <div className="font-medium text-ink-800">Citations for free</div>
              <div className="mt-1 text-ink-600">
                Every RAG chunk carries page_start / page_end. Click to jump back to the source.
              </div>
            </li>
            <li className="rounded-lg border border-ink-200 bg-white p-3">
              <div className="font-medium text-ink-800">Self-hosted</div>
              <div className="mt-1 text-ink-600">
                MIT-licensed Docling, runs on your machine. PDPA / GDPR / CCPA-friendly by design.
              </div>
            </li>
            <li className="rounded-lg border border-ink-200 bg-white p-3">
              <div className="font-medium text-ink-800">Quality signals</div>
              <div className="mt-1 text-ink-600">
                Heuristics flag scanned-only / sparse-table / flat-structure failure modes
                <em> before</em> they corrupt your RAG.
              </div>
            </li>
          </ul>
        </main>
      </div>
    );
  }

  // ---------- Loading state ----------
  if (loading) {
    return (
      <div className="flex min-h-full flex-col">
        <Header />
        <main className="flex flex-1 items-center justify-center text-sm text-ink-600">
          Extracting…
        </main>
      </div>
    );
  }

  // ---------- Result state ----------
  return (
    <div className="flex h-screen flex-col">
      <Header
        fileName={doc!.source_name}
        pageCount={doc!.page_count}
        tableCount={doc!.tables.length}
        engine={doc!.extractor.engine}
        elapsedMs={doc!.extractor.elapsed_ms}
        onReset={reset}
      />
      {doc!.extractor.note ? (
        <div className="border-b border-amber-200 bg-amber-50 px-5 py-2 text-xs text-amber-900">
          {doc!.extractor.note}
        </div>
      ) : null}
      <div className="flex flex-1 overflow-hidden">
        <section className="w-1/2 border-r border-ink-200">
          {pdfBlob ? (
            <PdfViewer ref={pdfRef} file={pdfBlob} />
          ) : (
            <div className="flex h-full items-center justify-center bg-ink-100 p-8 text-center text-sm text-ink-400">
              No PDF preview for this source. Upload a real PDF to see side-by-side.
            </div>
          )}
        </section>
        <section className="w-1/2">
          <ExtractionPanel
            doc={doc!}
            onJumpToPage={(p) => pdfRef.current?.scrollToPage(p)}
          />
        </section>
      </div>
    </div>
  );
}
