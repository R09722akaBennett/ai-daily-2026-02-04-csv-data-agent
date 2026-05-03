"use client";

import { useState } from "react";

import type { ExtractedDocumentJson } from "@/lib/types";

import { ChunksPanel } from "./ChunksPanel";
import { MarkdownPanel } from "./MarkdownPanel";
import { QualityPanel } from "./QualityPanel";
import { SectionsPanel } from "./SectionsPanel";
import { TablesPanel } from "./TablesPanel";

const TABS = ["Markdown", "Tables", "RAG", "Sections", "Quality"] as const;
type Tab = (typeof TABS)[number];

interface Props {
  doc: ExtractedDocumentJson;
  onJumpToPage?: (page: number) => void;
}

function downloadText(filename: string, text: string, mime: string) {
  const blob = new Blob([text], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExtractionPanel({ doc, onJumpToPage }: Props) {
  const [tab, setTab] = useState<Tab>("Markdown");
  const baseName = doc.source_name.replace(/\.[^/.]+$/, "");

  return (
    <div className="flex h-full flex-col">
      <div className="flex border-b border-ink-200 bg-white">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={[
              "px-4 py-2 text-sm",
              tab === t
                ? "border-b-2 border-ink-800 font-medium text-ink-800"
                : "text-ink-400 hover:text-ink-800",
            ].join(" ")}
          >
            {t}
            {t === "Tables" ? (
              <span className="ml-1 text-xs text-ink-400">{doc.tables.length}</span>
            ) : null}
            {t === "RAG" ? (
              <span className="ml-1 text-xs text-ink-400">{doc.rag_chunks?.length ?? 0}</span>
            ) : null}
            {t === "Quality" ? (
              <span className="ml-1 text-xs text-ink-400">{doc.warnings.length}</span>
            ) : null}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 px-3">
          <button
            onClick={() => downloadText(`${baseName}.json`, JSON.stringify(doc, null, 2), "application/json")}
            className="rounded-md border border-ink-200 px-2.5 py-1 text-xs text-ink-800 hover:bg-ink-50"
          >
            Download full JSON
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto bg-ink-50/40 p-4">
        {tab === "Markdown" ? (
          <MarkdownPanel
            markdown={doc.markdown}
            onDownload={() => downloadText(`${baseName}.md`, doc.markdown, "text/markdown")}
          />
        ) : null}
        {tab === "Tables" ? (
          <TablesPanel tables={doc.tables} onJumpToPage={onJumpToPage} />
        ) : null}
        {tab === "RAG" ? (
          <ChunksPanel
            chunks={doc.rag_chunks ?? []}
            sourceName={doc.source_name}
            onJumpToPage={onJumpToPage}
          />
        ) : null}
        {tab === "Sections" ? (
          <SectionsPanel sections={doc.sections} onJumpToPage={onJumpToPage} />
        ) : null}
        {tab === "Quality" ? <QualityPanel warnings={doc.warnings} /> : null}
      </div>
    </div>
  );
}
