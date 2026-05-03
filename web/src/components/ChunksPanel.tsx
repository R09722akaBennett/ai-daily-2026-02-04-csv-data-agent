"use client";

import type { RagChunk } from "@/lib/types";

function chunksToJsonl(chunks: RagChunk[], sourceName: string): string {
  return (
    chunks
      .map((c) =>
        JSON.stringify({
          chunk_id: c.chunk_id,
          text: c.text,
          metadata: {
            source_name: sourceName,
            heading_path: c.heading_path,
            page_start: c.page_start,
            page_end: c.page_end,
            token_estimate: c.token_estimate,
          },
        }),
      )
      .join("\n") + "\n"
  );
}

function downloadJsonl(filename: string, body: string) {
  const blob = new Blob([body], { type: "application/x-ndjson;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

interface Props {
  chunks: RagChunk[];
  sourceName: string;
  onJumpToPage?: (page: number) => void;
}

export function ChunksPanel({ chunks, sourceName, onJumpToPage }: Props) {
  if (!chunks.length) {
    return <div className="text-sm text-ink-400">RAG chunks were not requested.</div>;
  }
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs text-ink-400">
          {chunks.length} chunks · ready for embedding / vector ingest
        </span>
        <button
          onClick={() =>
            downloadJsonl(
              `${sourceName.replace(/\.[^/.]+$/, "")}.chunks.jsonl`,
              chunksToJsonl(chunks, sourceName),
            )
          }
          className="rounded-md border border-ink-200 bg-white px-2.5 py-1 text-xs text-ink-800 hover:bg-ink-50"
        >
          Download .jsonl
        </button>
      </div>
      <ul className="space-y-3">
        {chunks.map((c) => {
          const path = c.heading_path.join(" > ") || "(unsectioned)";
          const pageLabel =
            c.page_start === c.page_end ? `p.${c.page_start}` : `p.${c.page_start}–${c.page_end}`;
          return (
            <li key={c.chunk_id} className="rounded-lg border border-ink-200 bg-white">
              <div className="flex items-center justify-between border-b border-ink-200 px-3 py-1.5 text-xs">
                <span className="text-ink-800">{path}</span>
                <div className="flex items-center gap-2 text-ink-400">
                  <span>~{c.token_estimate} tokens</span>
                  {c.page_start ? (
                    <button
                      onClick={() => onJumpToPage?.(c.page_start)}
                      className="rounded bg-ink-100 px-1.5 py-0.5 text-ink-800 hover:bg-ink-200"
                    >
                      {pageLabel} →
                    </button>
                  ) : (
                    <span>{pageLabel}</span>
                  )}
                </div>
              </div>
              <pre className="whitespace-pre-wrap break-words p-3 text-xs text-ink-800">{c.text}</pre>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
