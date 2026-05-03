import type { ExtractedDocumentJson } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(`${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function unwrap(resp: Response): Promise<unknown> {
  if (resp.ok) return resp.json();
  let detail = resp.statusText;
  try {
    const body = await resp.json();
    if (body?.detail) detail = String(body.detail);
  } catch {
    // ignore
  }
  throw new ApiError(resp.status, detail);
}

export async function extractFile(
  file: File,
  opts: { rag?: boolean; signal?: AbortSignal } = {},
): Promise<ExtractedDocumentJson> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams({ rag: String(opts.rag ?? true) });
  const resp = await fetch(`${API_URL}/api/extract?${params}`, {
    method: "POST",
    body: form,
    signal: opts.signal,
  });
  return (await unwrap(resp)) as ExtractedDocumentJson;
}

export async function loadDemo(signal?: AbortSignal): Promise<ExtractedDocumentJson> {
  const resp = await fetch(`${API_URL}/api/demo`, { signal });
  return (await unwrap(resp)) as ExtractedDocumentJson;
}

export async function health(): Promise<{ status: string }> {
  const resp = await fetch(`${API_URL}/api/health`);
  return (await unwrap(resp)) as { status: string };
}
