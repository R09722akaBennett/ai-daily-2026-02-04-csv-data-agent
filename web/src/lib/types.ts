// Mirror of app/core/types.py — the wire contract from FastAPI's /api/extract & /api/demo.
// Keep field names in sync with `to_full_json()` in app/core/exports.py.

export type Severity = "info" | "warning" | "error";

export interface QualitySignal {
  code: string;
  severity: Severity;
  message: string;
  suggestion?: string | null;
}

export interface ExtractedSection {
  heading: string | null;
  level: number;
  heading_path: string[];
  text: string;
  page_start: number;
  page_end: number;
}

export interface ExtractedTable {
  index: number;
  page: number;
  n_rows: number;
  n_cols: number;
  has_header: boolean;
  caption: string | null;
  rows: string[][];
}

export interface RagChunk {
  chunk_id: string;
  text: string;
  heading_path: string[];
  page_start: number;
  page_end: number;
  token_estimate: number;
}

export interface ExtractorInfo {
  engine: string;
  elapsed_ms?: number;
  options?: Record<string, unknown>;
  note?: string;
}

export interface ExtractedDocumentJson {
  source_name: string;
  page_count: number;
  metadata: Record<string, unknown>;
  extractor: ExtractorInfo;
  warnings: QualitySignal[];
  sections: ExtractedSection[];
  tables: ExtractedTable[];
  markdown: string;
  rag_chunks?: RagChunk[];
}
