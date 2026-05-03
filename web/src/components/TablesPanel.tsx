"use client";

import type { ExtractedTable } from "@/lib/types";

function rowsToCsv(rows: string[][]): string {
  return rows
    .map((row) =>
      row
        .map((cell) => {
          const s = (cell ?? "").toString();
          // Quote per RFC 4180 when needed.
          if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
          return s;
        })
        .join(","),
    )
    .join("\n");
}

function downloadCsv(name: string, rows: string[][]) {
  const blob = new Blob([rowsToCsv(rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

interface Props {
  tables: ExtractedTable[];
  onJumpToPage?: (page: number) => void;
}

export function TablesPanel({ tables, onJumpToPage }: Props) {
  if (tables.length === 0) {
    return (
      <div className="text-sm text-ink-400">
        No tables detected. (Expected for prose-only documents.)
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {tables.map((t) => {
        const filename = `table-${String(t.index).padStart(2, "0")}-p${String(t.page || 0).padStart(3, "0")}.csv`;
        const headerRow = t.has_header && t.rows.length > 0 ? t.rows[0] : null;
        const bodyRows = headerRow ? t.rows.slice(1) : t.rows;
        return (
          <div key={t.index} className="rounded-lg border border-ink-200 bg-white">
            <div className="flex items-center justify-between border-b border-ink-200 px-3 py-2">
              <div className="text-sm">
                <span className="font-medium">Table #{t.index}</span>{" "}
                <span className="text-ink-400">
                  · {t.n_rows}×{t.n_cols}
                </span>
                {t.page ? (
                  <button
                    onClick={() => onJumpToPage?.(t.page)}
                    className="ml-2 rounded bg-ink-100 px-1.5 py-0.5 text-xs text-ink-800 hover:bg-ink-200"
                  >
                    page {t.page} →
                  </button>
                ) : null}
                {t.caption ? (
                  <div className="mt-0.5 text-xs text-ink-400">{t.caption}</div>
                ) : null}
              </div>
              <button
                onClick={() => downloadCsv(filename, t.rows)}
                className="rounded-md border border-ink-200 px-2.5 py-1 text-xs text-ink-800 hover:bg-ink-50"
              >
                Download CSV
              </button>
            </div>
            <div className="max-h-64 overflow-auto">
              <table className="min-w-full text-xs">
                {headerRow ? (
                  <thead className="bg-ink-50">
                    <tr>
                      {headerRow.map((cell, i) => (
                        <th key={i} className="border-b border-ink-200 px-2 py-1 text-left font-medium text-ink-800">
                          {cell}
                        </th>
                      ))}
                    </tr>
                  </thead>
                ) : null}
                <tbody>
                  {bodyRows.map((row, ri) => (
                    <tr key={ri} className={ri % 2 === 0 ? "bg-white" : "bg-ink-50/40"}>
                      {row.map((cell, ci) => (
                        <td key={ci} className="border-b border-ink-100 px-2 py-1 align-top text-ink-800">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
