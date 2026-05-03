"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Worker is served from the matching pdfjs-dist version's CDN — keeps us off the
// "I forgot to copy the worker into /public" footgun.
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

export interface PdfViewerHandle {
  scrollToPage: (page: number) => void;
}

interface Props {
  file: Blob | null;
  width?: number;
}

export const PdfViewer = forwardRef<PdfViewerHandle, Props>(function PdfViewer(
  { file, width = 720 },
  ref,
) {
  const [numPages, setNumPages] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  useImperativeHandle(ref, () => ({
    scrollToPage(page: number) {
      const target = pageRefs.current.get(page);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    },
  }));

  // Fresh blob → fresh page refs.
  useEffect(() => {
    pageRefs.current.clear();
    setError(null);
    setNumPages(0);
  }, [file]);

  if (!file) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-ink-400">
        Upload a PDF to see it side-by-side with the extraction.
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-full overflow-y-auto bg-ink-100 p-4">
      <Document
        file={file}
        onLoadSuccess={({ numPages: n }) => setNumPages(n)}
        onLoadError={(err) => setError(err.message)}
        loading={<div className="text-ink-400">Rendering PDF…</div>}
      >
        {error ? (
          <div className="text-sm text-red-600">PDF render failed: {error}</div>
        ) : (
          Array.from({ length: numPages }, (_, i) => i + 1).map((p) => (
            <div
              key={p}
              ref={(el) => {
                if (el) pageRefs.current.set(p, el);
                else pageRefs.current.delete(p);
              }}
              className="mb-4 flex flex-col items-center"
            >
              <div className="mb-1 text-xs text-ink-400">Page {p}</div>
              <Page
                pageNumber={p}
                width={width}
                renderAnnotationLayer={false}
                renderTextLayer={false}
                className="shadow"
              />
            </div>
          ))
        )}
      </Document>
    </div>
  );
});
