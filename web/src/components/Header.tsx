interface Props {
  fileName?: string;
  pageCount?: number;
  tableCount?: number;
  engine?: string;
  elapsedMs?: number;
  onReset?: () => void;
}

export function Header({ fileName, pageCount, tableCount, engine, elapsedMs, onReset }: Props) {
  return (
    <header className="flex items-center justify-between border-b border-ink-200 bg-white px-5 py-3">
      <div className="flex items-baseline gap-3">
        <h1 className="text-lg font-semibold text-ink-900">KDoc IDP</h1>
        <span className="hidden text-xs text-ink-400 sm:inline">
          Document → LLM-ready data, self-hosted via Docling
        </span>
      </div>
      <div className="flex items-center gap-4 text-xs text-ink-600">
        {fileName ? (
          <>
            <span className="font-mono">{fileName}</span>
            <span className="text-ink-400">·</span>
            <span>{pageCount ?? 0} pages</span>
            <span className="text-ink-400">·</span>
            <span>{tableCount ?? 0} tables</span>
            {engine ? (
              <>
                <span className="text-ink-400">·</span>
                <span className="rounded bg-ink-100 px-1.5 py-0.5">
                  {engine}
                  {elapsedMs ? ` · ${elapsedMs} ms` : ""}
                </span>
              </>
            ) : null}
            {onReset ? (
              <button
                onClick={onReset}
                className="ml-2 rounded-md border border-ink-200 px-2.5 py-1 text-ink-800 hover:bg-ink-50"
              >
                New file
              </button>
            ) : null}
          </>
        ) : null}
      </div>
    </header>
  );
}
