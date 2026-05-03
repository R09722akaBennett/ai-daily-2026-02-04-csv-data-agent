"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MarkdownPanel({
  markdown,
  onDownload,
}: {
  markdown: string;
  onDownload: () => void;
}) {
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs text-ink-400">{markdown.length.toLocaleString()} chars</span>
        <button
          onClick={onDownload}
          className="rounded-md border border-ink-200 bg-white px-2.5 py-1 text-xs text-ink-800 hover:bg-ink-50"
        >
          Download .md
        </button>
      </div>
      <article className="prose prose-sm max-w-none prose-headings:font-semibold prose-pre:bg-ink-50 prose-pre:text-ink-800 prose-table:text-xs">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown || "_(empty)_"}</ReactMarkdown>
      </article>
    </div>
  );
}
