// ============================================================
// API base configuration
// ============================================================
//
// In development Vite proxies /api/* and /health to localhost:8000,
// so API_BASE is empty (same-origin).  This avoids all CORS issues.
//
// In production set VITE_API_URL to your deployed backend URL.
// ============================================================

export const API_BASE: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? body?.error?.message ?? `HTTP ${res.status}`);
  }

  const json: ApiResponse<T> = await res.json();
  if (!json.success) {
    throw new Error(json.error?.message ?? 'Unknown API error');
  }
  return json.data as T;
}

/** Form-data upload — browser sets the correct multipart boundary */
export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  const json: ApiResponse<T> = await res.json();
  if (!json.success) throw new Error(json.error?.message ?? 'Upload failed');
  return json.data as T;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
