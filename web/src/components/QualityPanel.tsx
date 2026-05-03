import type { QualitySignal } from "@/lib/types";

const COLORS: Record<QualitySignal["severity"], string> = {
  info: "border-blue-200 bg-blue-50 text-blue-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  error: "border-red-200 bg-red-50 text-red-900",
};

export function QualityPanel({ warnings }: { warnings: QualitySignal[] }) {
  if (warnings.length === 0) {
    return <div className="text-sm text-ink-400">No quality signals.</div>;
  }
  return (
    <ul className="space-y-3">
      {warnings.map((w, i) => (
        <li key={`${w.code}-${i}`} className={`rounded-lg border px-3 py-2 ${COLORS[w.severity]}`}>
          <div className="flex items-center gap-2">
            <span className="rounded bg-white/60 px-1.5 py-0.5 text-xs font-mono uppercase">
              {w.severity}
            </span>
            <span className="font-medium">{w.code}</span>
          </div>
          <div className="mt-1 text-sm">{w.message}</div>
          {w.suggestion ? (
            <div className="mt-1 text-xs opacity-80">→ {w.suggestion}</div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
