"use client";

import type { ExtractedSection } from "@/lib/types";

interface Props {
  sections: ExtractedSection[];
  onJumpToPage?: (page: number) => void;
}

export function SectionsPanel({ sections, onJumpToPage }: Props) {
  if (!sections.length) {
    return <div className="text-sm text-ink-400">No sections detected.</div>;
  }
  return (
    <ul className="space-y-4">
      {sections.map((s, i) => {
        const path = s.heading_path.join(" > ") || "(unsectioned)";
        const pageLabel =
          s.page_start === s.page_end ? `p.${s.page_start}` : `p.${s.page_start}–${s.page_end}`;
        return (
          <li key={`${s.heading}-${i}`} className="rounded-lg border border-ink-200 bg-white p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-ink-800">{path}</span>
              <div className="flex items-center gap-2 text-ink-400">
                <span>level {s.level}</span>
                {s.page_start ? (
                  <button
                    onClick={() => onJumpToPage?.(s.page_start)}
                    className="rounded bg-ink-100 px-1.5 py-0.5 text-ink-800 hover:bg-ink-200"
                  >
                    {pageLabel} →
                  </button>
                ) : (
                  <span>{pageLabel}</span>
                )}
              </div>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ink-800">{s.text}</p>
          </li>
        );
      })}
    </ul>
  );
}
