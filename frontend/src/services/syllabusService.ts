/**
 * Syllabus Service
 * ---------------------------------------------------------------------------
 * All calls go through the Vite proxy (/api/*) — no CORS issues.
 * Every mutating request (upload, delete) sends X-User-Role header
 * so the backend can enforce faculty-only access.
 * ---------------------------------------------------------------------------
 */

// ── Role header helper ────────────────────────────────────────────────────────

/** Read the current role from sessionStorage (matches RoleContext). */
function getCurrentRole(): string {
  try { return sessionStorage.getItem('courseai_role') ?? 'faculty'; } catch { return 'faculty'; }
}

function roleHeaders(): HeadersInit {
  return { 'X-User-Role': getCurrentRole() };
}

// ── Backend shapes ────────────────────────────────────────────────────────────

export interface BackendDocument {
  document_id: number;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  original_filename: string;
  file_type: string;
  file_size: number;
  course_id: number | null;
  course_name: string | null;
  uploaded_at: string;
  error_message: string | null;
  extracted_units: number;
  extracted_topics: number;
  extracted_outcomes: number;
  extracted_textbooks: number;
  file_hash: string | null;
}

interface UploadOut {
  document_id: number;
  status: string;
  filename: string;
  file_size: number;
}

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path);  // GET — no role enforcement needed
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? body?.error?.message ?? `HTTP ${res.status}`);
  }
  const json: Envelope<T> = await res.json();
  if (!json.success || json.data === undefined) {
    throw new Error(json.error?.message ?? 'API error');
  }
  return json.data;
}

const delay = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

// ── Service ───────────────────────────────────────────────────────────────────

export const syllabusService = {
  /** List all uploaded documents, optionally filtered by course. */
  async listDocuments(courseId?: number): Promise<BackendDocument[]> {
    const qs = courseId != null ? `?course_id=${courseId}` : '';
    try {
      return await apiGet<BackendDocument[]>(`/api/syllabus${qs}`);
    } catch (err) {
      console.warn('[syllabusService] listDocuments failed:', err);
      return [];
    }
  },

  /** Poll a single document's status. */
  async getDocumentStatus(documentId: number): Promise<BackendDocument> {
    return apiGet<BackendDocument>(`/api/syllabus/${documentId}/status`);
  },

  /** Return the URL to download / open a document inline. */
  getDownloadUrl(documentId: number): string {
    return `/api/syllabus/${documentId}/download`;
  },

  /** Delete a document and remove its vectorised content. */
  async deleteDocument(documentId: number): Promise<void> {
    const res = await fetch(`/api/syllabus/${documentId}`, {
      method: 'DELETE',
      headers: roleHeaders(),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail ?? `HTTP ${res.status}`);
    }
  },

  /**
   * Upload a file and poll until processing completes.
   * Calls onProgress(stepLabel, percent) throughout.
   * Throws with message "DUPLICATE" if the file already exists.
   */
  async processFile(
    file: File,
    onProgress: (step: string, pct: number) => void,
    courseId?: number,
  ): Promise<{ units: number; topics: number; courseOutcomes: number; textbooks: number; documentId: number }> {
    // ── Upload ────────────────────────────────────────────────────────────
    onProgress('Uploading file...', 8);

    const form = new FormData();
    form.append('file', file);
    if (courseId != null) form.append('course_id', String(courseId));

    const uploadRes = await fetch('/api/syllabus/upload', {
      method: 'POST',
      headers: roleHeaders(),   // sends X-User-Role
      body: form,
    });

    if (uploadRes.status === 409) {
      // Duplicate file
      const body = await uploadRes.json().catch(() => ({}));
      throw new Error('DUPLICATE:' + (body?.detail ?? 'This file already exists for this course.'));
    }

    if (uploadRes.status === 403) {
      const body = await uploadRes.json().catch(() => ({}));
      throw new Error('FORBIDDEN:' + (body?.detail ?? 'Access denied.'));
    }

    if (!uploadRes.ok) {
      const body = await uploadRes.json().catch(() => ({}));
      throw new Error(body?.detail ?? `Upload failed (HTTP ${uploadRes.status})`);
    }

    const uploadEnv: Envelope<UploadOut> = await uploadRes.json();
    if (!uploadEnv.success || !uploadEnv.data) {
      throw new Error(uploadEnv.error?.message ?? 'Upload error');
    }

    const docId = uploadEnv.data.document_id;
    onProgress('Analyzing syllabus structure...', 20);

    // ── Poll until completed or failed ────────────────────────────────────
    const stepLabels = [
      'Extracting unit information...',
      'Identifying topics...',
      'Mapping course outcomes...',
      'Indexing content...',
      'Finalizing...',
    ];

    for (let i = 0; i < 60; i++) {          // up to ~90 s
      await delay(1500);

      let status: BackendDocument;
      try {
        status = await this.getDocumentStatus(docId);
      } catch {
        continue;                             // transient error — keep polling
      }

      if (status.status === 'completed') {
        onProgress('Complete!', 100);
        return {
          units: status.extracted_units,
          topics: status.extracted_topics,
          courseOutcomes: status.extracted_outcomes,
          textbooks: status.extracted_textbooks,
          documentId: docId,
        };
      }

      if (status.status === 'failed') {
        throw new Error(status.error_message ?? 'Processing failed on the server.');
      }

      // Still processing — animate progress bar
      const pct = Math.min(22 + i * 1.3, 94);
      const label = stepLabels[Math.min(Math.floor(i / 12), stepLabels.length - 1)];
      onProgress(label, pct);
    }

    throw new Error('Processing timed out. The file may still be indexing in the background.');
  },
};
