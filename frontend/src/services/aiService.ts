/**
 * AI Chat Service
 * ---------------------------------------------------------------------------
 * Sends every message to POST /api/chat.
 *
 * In development Vite proxies /api/* → http://localhost:8000/api/*,
 * so no CORS issue ever occurs.
 *
 * In production set VITE_API_URL to point to the deployed backend and
 * the requests will go there directly.
 *
 * There is NO mock fallback and NO hardcoded answers.
 * Every question goes to the real LLM backend.
 * ---------------------------------------------------------------------------
 */

// Use a relative path in dev (proxied by Vite) or an absolute URL in prod.
// When VITE_API_URL is not set, '' means "same origin" which Vite proxies.
const API_BASE: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';

const isDev = import.meta.env.DEV;

// ── Public types ──────────────────────────────────────────────────────────────

export interface Resource {
  resource_type: string;
  title: string;
  author?: string;
  url?: string;
}

export interface Citation {
  id: string;
  filename: string;
  courseId?: string;
  courseCode?: string;
  courseName?: string;
  documentId?: number;
  unit?: string;
  unitNumber?: number;
  topicId?: string;
  topicName?: string;
  page?: string;
}

export interface AIChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations: Citation[];
  resources: Resource[];
}

export interface HistoryEntry {
  role: 'user' | 'assistant';
  content: string;
}

// ── Internal backend shapes ───────────────────────────────────────────────────

interface BackendCitation {
  filename?: string;
  course_id?: number | null;
  course_code?: string | null;
  course_name?: string | null;
  document_id?: number | null;
  page?: number | null;
  unit?: string | null;
  unit_number?: number | null;
  topic_id?: number | null;
  topic_name?: string | null;
  text?: string | null;
}

interface BackendResource {
  resource_type: string;
  title: string;
  author?: string | null;
  url?: string | null;
}

interface BackendChatData {
  course_id: number | null;
  message: string;
  answer: string;
  citations: BackendCitation[];
  resources: BackendResource[];
  suggested_questions: string[];
}

interface BackendEnvelope {
  success: boolean;
  data?: BackendChatData;
  error?: { code: string; message: string };
}

interface CourseContext {
  id: number;
  course_name: string;
  course_code: string;
  regulation: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function genId(): string {
  return Math.random().toString(36).substring(2, 11);
}

const delay = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

/** Build an AbortSignal that times out after `ms` milliseconds.
 *  Uses the native AbortSignal.timeout() when available (Chrome 103+, FF 100+)
 *  and falls back to a manual controller for older engines. */
function timeoutSignal(ms: number): AbortSignal {
  if (typeof AbortSignal !== 'undefined' && 'timeout' in AbortSignal) {
    return AbortSignal.timeout(ms);
  }
  const ctrl = new AbortController();
  setTimeout(() => ctrl.abort(), ms);
  return ctrl.signal;
}

function normalise(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

async function resolveCourseContext(
  question: string,
  selectedCourseId: string,
  selectedRegulation: string,
): Promise<{ courseId: string; regulation: string }> {
  const explicitRegulation = question.match(/\bR[-\s]?(\d{2,4})\b/i)?.[1];
  const explicitCode = question.match(/\b\d{2}[A-Z]{2,4}\d{3}[A-Z]?\b/i)?.[0].toUpperCase();
  const regulation = explicitRegulation ? `R${explicitRegulation}` : selectedRegulation;
  const response = await fetch(
    `${API_BASE}/api/courses${regulation ? `?regulation=${encodeURIComponent(regulation)}` : ''}`,
  );
  if (!response.ok) return { courseId: explicitRegulation || explicitCode ? '' : selectedCourseId, regulation };

  const envelope = await response.json() as { success: boolean; data?: CourseContext[] };
  const courses = envelope.success && Array.isArray(envelope.data) ? envelope.data : [];
  const normalisedQuestion = normalise(question);
  const matched = courses.find(course =>
    (explicitCode && course.course_code.toUpperCase() === explicitCode) ||
    normalisedQuestion.includes(normalise(course.course_name)),
  );

  if (matched) {
    return { courseId: String(matched.id), regulation: matched.regulation };
  }

  // An explicit regulation must never inherit a course from another regulation.
  return { courseId: explicitRegulation || explicitCode ? '' : selectedCourseId, regulation };
}

// ── Service ───────────────────────────────────────────────────────────────────

export const aiService = {
  /**
   * Send a user message to POST /api/chat and return the AI response.
   *
   * @param question   Any natural-language question.
   * @param courseId   String representation of the numeric backend course id.
   * @param history    Up to 6 previous turns for follow-up context.
   * @param onTyping   Called with accumulated text to simulate streaming.
   */
  async sendMessage(
    question: string,
    courseId: string,
    regulation = '',
    history: HistoryEntry[] = [],
    onTyping?: (partialText: string) => void,
  ): Promise<AIChatMessage> {
    const explicitRegulation = question.match(/\bR[-\s]?(\d{2,4})\b/i)?.[1];
    const explicitCode = question.match(/\b\d{2}[A-Z]{2,4}\d{3}[A-Z]?\b/i);
    let resolvedCourseId = explicitRegulation || explicitCode ? '' : courseId;
    let resolvedRegulation = explicitRegulation ? `R${explicitRegulation}` : regulation;
    try {
      ({ courseId: resolvedCourseId, regulation: resolvedRegulation } =
        await resolveCourseContext(question, courseId, regulation));
    } catch (err) {
      console.warn('[aiService] Course context resolution failed:', err);
    }

    const numericId = parseInt(resolvedCourseId, 10);

    const endpoint = `${API_BASE}/api/chat`;
    const payload = {
      course_id: isNaN(numericId) ? null : numericId,
      regulation: resolvedRegulation || null,
      message: question,
      history: history.slice(-6),
    };

    if (isDev) {
      console.log('[aiService] POST', endpoint, '| course_id:', payload.course_id);
    }

    let response: Response;
    try {
      response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: timeoutSignal(90_000),  // 90 s — LLM generation can take time
      });
    } catch (networkErr) {
      // This block is only reached for genuine network failures
      // (connection refused, DNS failure, timeout, etc.)
      const msg = networkErr instanceof Error ? networkErr.message : String(networkErr);
      console.error('[aiService] Network error:', msg, '| endpoint:', endpoint);

      return {
        id: genId(),
        role: 'assistant',
        content:
          `⚠️ **Cannot connect to the backend** (${endpoint})\n\n` +
          `Error: \`${msg}\`\n\n` +
          'Make sure the backend server is running:\n\n' +
          '```\ncd course-content-agent-backend\n' +
          '.venv\\Scripts\\python.exe run.py\n```',
        timestamp: new Date(),
        citations: [],
        resources: [],
      };
    }

    if (isDev) {
      console.log('[aiService] Response status:', response.status, response.statusText);
    }

    // HTTP-level error (4xx / 5xx)
    if (!response.ok) {
      let detail = `HTTP ${response.status} ${response.statusText}`;
      try {
        const body = await response.json();
        detail = body?.detail ?? body?.error?.message ?? detail;
      } catch { /* body not JSON */ }
      console.error('[aiService] Backend HTTP error:', detail);
      return {
        id: genId(),
        role: 'assistant',
        content: `The backend returned an error: **${detail}**. Please try again.`,
        timestamp: new Date(),
        citations: [],
        resources: [],
      };
    }

    // Parse JSON envelope
    let envelope: BackendEnvelope;
    try {
      envelope = await response.json();
    } catch (parseErr) {
      console.error('[aiService] Failed to parse JSON:', parseErr);
      return {
        id: genId(),
        role: 'assistant',
        content: 'The backend returned a response that could not be parsed. Please try again.',
        timestamp: new Date(),
        citations: [],
        resources: [],
      };
    }

    if (isDev) {
      console.log('[aiService] success:', envelope.success, '| answer length:', envelope.data?.answer?.length ?? 0);
    }

    if (!envelope.success || !envelope.data) {
      const msg = envelope.error?.message ?? 'Unknown backend error.';
      console.error('[aiService] Backend returned success=false:', msg);
      return {
        id: genId(),
        role: 'assistant',
        content: `Backend error: ${msg}`,
        timestamp: new Date(),
        citations: [],
        resources: [],
      };
    }

    const data = envelope.data;
    const content = data.answer ?? '';

    // Streaming simulation — yield control every few characters
    if (onTyping && content) {
      const chars = content.split('');
      let accumulated = '';
      for (let i = 0; i < chars.length; i++) {
        accumulated += chars[i];
        onTyping(accumulated);
        if (i % 4 === 0) await delay(8);
      }
    }

    const citations: Citation[] = (data.citations ?? []).map(c => ({
      id: genId(),
      filename: c.filename ?? 'Course Syllabus',
      courseId: c.course_id != null ? String(c.course_id) : undefined,
      courseCode: c.course_code ?? undefined,
      courseName: c.course_name ?? undefined,
      documentId: c.document_id ?? undefined,
      unit: c.unit ?? undefined,
      unitNumber: c.unit_number ?? undefined,
      topicId: c.topic_id != null ? String(c.topic_id) : undefined,
      topicName: c.topic_name ?? undefined,
      page: c.page != null ? String(c.page) : undefined,
    }));

    const resources: Resource[] = (data.resources ?? []).map(r => ({
      resource_type: r.resource_type,
      title: r.title,
      author: r.author ?? undefined,
      url: r.url ?? undefined,
    }));

    return {
      id: genId(),
      role: 'assistant',
      content,
      timestamp: new Date(),
      citations,
      resources,
    };
  },

  getSuggestedQuestions(_courseId: string): string[] {
    return [
      'What is Unit 3 about?',
      'Explain binary trees in simple words.',
      'Compare stacks and queues.',
      'Which textbook should I use for trees?',
      'Give me a study plan for this course.',
      'What are the course outcomes?',
    ];
  },
};
