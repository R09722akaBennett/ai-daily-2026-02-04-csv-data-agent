"use client";

import { useCallback, useRef, useState } from "react";

const ACCEPTED = ".pdf,.docx,.pptx,.xlsx,.html,.md,.png,.jpg,.jpeg";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function DropZone({ onFile, disabled }: Props) {
  const [hover, setHover] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setHover(false);
      if (disabled) return;
      const f = e.dataTransfer.files?.[0];
      if (f) onFile(f);
    },
    [onFile, disabled],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setHover(true);
      }}
      onDragLeave={() => setHover(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={[
        "rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition",
        hover ? "border-ink-800 bg-ink-50" : "border-ink-200 bg-white hover:bg-ink-50",
        disabled ? "opacity-50 cursor-not-allowed" : "",
      ].join(" ")}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
        disabled={disabled}
      />
      <div className="text-lg font-medium text-ink-800">
        Drop a document here, or click to choose
      </div>
      <div className="mt-2 text-sm text-ink-600">
        PDF · DOCX · PPTX · XLSX · HTML · PNG · JPG — up to 50 MB
      </div>
      <div className="mt-1 text-xs text-ink-400">
        Files are uploaded to your local backend. Nothing leaves your machine.
      </div>
    </div>
  );
}
