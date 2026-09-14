/**
 * Course Service
 * ---------------------------------------------------------------------------
 * Fetches course data from the backend via the Vite proxy (/api/*).
 * Falls back to mock data only when the backend returns a network error.
 *
 * KEY POINT: The backend and frontend use different field names.
 * mapListItem()   converts the backend list shape → frontend Course shape.
 * mapDetailItem() converts the backend detail shape → frontend Course shape.
 * ---------------------------------------------------------------------------
 */
import type { Course, Unit, Topic, CourseOutcome, Textbook, ReferenceBook, COPOMapping, FilterOptions } from '../types';
import { mockCourses } from '../data/mockData';
import { API_BASE } from './api';

// ── Backend list shape (GET /api/courses) ─────────────────────────────────────

interface BackendCourseList {
  id: number;
  course_name: string;
  course_code: string;
  program: string;
  department: string;
  year: string;
  semester: string;
  regulation: string;
  credits: number;
  total_hours: number;
  description: string;
  prerequisites: string;          // comma-separated
  unit_count: number;
  topic_count: number;
  co_count: number;
  textbook_count: number;
  status: string;
  created_at: string;
}

// ── Backend detail shape (GET /api/courses/:id) ───────────────────────────────

interface BackendTopic {
  id: number;
  unit_id: number;
  topic_name: string;
  topic_order: number;
  description: string | null;
}

interface BackendUnit {
  id: number;
  course_id: number;
  unit_number: number;
  unit_name: string;
  hours: number;
  co_mapping: string | null;    // e.g. "CO1" or "CO1, CO2"
  description: string | null;
  topics: BackendTopic[];
}

interface BackendOutcome {
  id: number;
  course_id: number;
  co_number: string;
  description: string;
  bloom_level: string | null;
}

interface BackendTextbook {
  id: number;
  course_id: number;
  title: string;
  author: string;
  edition: string | null;
  publisher: string | null;
  year: string | null;
  isbn: string | null;
  book_type: 'textbook' | 'reference';
}

interface BackendCourseDetail {
  id: number;
  course_name: string;
  course_code: string;
  program: string;
  department: string;
  year: string;
  semester: string;
  regulation: string;
  credits: number;
  total_hours: number;
  description: string | null;
  prerequisites: string | null;
  created_at: string;
  units: BackendUnit[];
  outcomes: BackendOutcome[];
  textbooks: BackendTextbook[];
}

// ── Mappers ───────────────────────────────────────────────────────────────────

function prereqList(raw: string | null | undefined): string[] {
  if (!raw) return [];
  return raw.split(',').map(s => s.trim()).filter(Boolean);
}

function coMappingList(raw: string | null | undefined): string[] {
  if (!raw) return [];
  return raw.split(',').map(s => s.trim()).filter(Boolean);
}

/** Convert a backend list item to the lightweight frontend Course shape. */
function mapListItem(c: BackendCourseList): Course {
  return {
    id: String(c.id),
    name: c.course_name,
    code: c.course_code,
    program: c.program,
    department: c.department,
    year: c.year,
    semester: c.semester,
    regulation: c.regulation,
    credits: c.credits,
    totalHours: c.total_hours,
    description: c.description ?? '',
    prerequisites: prereqList(c.prerequisites),
    status: (c.status as Course['status']) ?? 'indexed',
    uploadedAt: c.created_at ?? new Date().toISOString(),
    // Stub placeholders — not needed for the list card
    units: Array.from({ length: c.unit_count }, (_, i) => ({
      id: `stub-unit-${i + 1}`,
      number: i + 1,
      title: '',
      hours: 0,
      topics: [],
      coMapping: [],
    })),
    courseOutcomes: Array.from({ length: c.co_count }, (_, i) => ({
      id: `stub-co-${i + 1}`,
      code: `CO${i + 1}`,
      description: '',
    })),
    textbooks: [],
    referenceBooks: [],
    mappings: [],
    unitCount: c.unit_count,
    topicCount: c.topic_count,
    textbookCount: c.textbook_count,
  };
}

/** Convert a backend detail response to the full frontend Course shape. */
function mapDetailItem(c: BackendCourseDetail): Course {
  // Map units + topics
  const units: Unit[] = (c.units ?? [])
    .sort((a, b) => a.unit_number - b.unit_number)
    .map(u => ({
      id: String(u.id),
      number: u.unit_number,
      title: u.unit_name,
      hours: u.hours,
      coMapping: coMappingList(u.co_mapping),
      description: u.description ?? undefined,
      topics: (u.topics ?? [])
        .sort((a, b) => a.topic_order - b.topic_order)
        .map((t): Topic => ({
          id: String(t.id),
          title: t.topic_name,
          // The backend doesn't store subtopics yet — leave empty
          subtopics: undefined,
        })),
    }));

  // Map outcomes
  const courseOutcomes: CourseOutcome[] = (c.outcomes ?? []).map(o => ({
    id: String(o.id),
    code: o.co_number,
    description: o.description,
    bloomLevel: o.bloom_level ?? undefined,
  }));

  // Split textbooks vs reference books
  const textbooks: Textbook[] = (c.textbooks ?? [])
    .filter(b => b.book_type === 'textbook')
    .map(b => ({
      id: String(b.id),
      title: b.title,
      author: b.author,
      edition: b.edition ?? '',
      publisher: b.publisher ?? '',
      year: b.year ?? undefined,
      isbn: b.isbn ?? undefined,
      courseIds: [String(c.id)],
      type: 'textbook' as const,
    }));

  const referenceBooks: ReferenceBook[] = (c.textbooks ?? [])
    .filter(b => b.book_type === 'reference')
    .map(b => ({
      id: String(b.id),
      title: b.title,
      author: b.author,
      edition: b.edition ?? '',
      publisher: b.publisher ?? '',
      year: b.year ?? undefined,
      isbn: b.isbn ?? undefined,
      courseIds: [String(c.id)],
      type: 'reference' as const,
    }));

  // Build CO-PO mappings — we don't have PO data in the detail endpoint yet,
  // so map from available COs with empty values (the mapping page uses /api/mapping)
  const mappings: COPOMapping[] = courseOutcomes.map(co => ({
    courseOutcomeId: co.code,
    mappings: {},
  }));

  return {
    id: String(c.id),
    name: c.course_name,
    code: c.course_code,
    program: c.program,
    department: c.department,
    year: c.year,
    semester: c.semester,
    regulation: c.regulation,
    credits: c.credits,
    totalHours: c.total_hours,
    description: c.description ?? '',
    prerequisites: prereqList(c.prerequisites),
    status: 'indexed',
    uploadedAt: c.created_at ?? new Date().toISOString(),
    units,
    courseOutcomes,
    textbooks,
    referenceBooks,
    mappings,
  };
}

// ── API helpers ───────────────────────────────────────────────────────────────

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: { 'Content-Type': 'application/json' } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json: Envelope<T> = await res.json();
  if (!json.success || json.data === undefined) {
    throw new Error(json.error?.message ?? 'API error');
  }
  return json.data;
}

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

// ── Public service ────────────────────────────────────────────────────────────

export const courseService = {
  async getAllCourses(filters?: FilterOptions): Promise<Course[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.program) params.set('program', filters.program);
      if (filters?.year) params.set('year', filters.year);
      if (filters?.regulation) params.set('regulation', filters.regulation);
      const qs = params.toString();
      const data = await get<BackendCourseList[]>(`/api/courses${qs ? `?${qs}` : ''}`);
      return data.map(mapListItem);
    } catch (err) {
      console.warn('[courseService] getAllCourses fell back to mock:', err);
      // Mock fallback
      await delay(300);
      let courses = [...mockCourses];
      if (filters?.program) courses = courses.filter(c => c.program === filters.program);
      if (filters?.year) courses = courses.filter(c => c.year === filters.year);
      if (filters?.regulation) courses = courses.filter(c => c.regulation === filters.regulation);
      return courses;
    }
  },

  async getCourseById(id: string): Promise<Course | null> {
    // id comes from the URL — it will be a numeric string like "1" when from backend,
    // or a slug like "cs201" when from mock fallback.
    const numId = parseInt(id, 10);

    if (!isNaN(numId)) {
      // Try backend first (always, no availability pre-check)
      try {
        const data = await get<BackendCourseDetail>(`/api/courses/${numId}`);
        return mapDetailItem(data);
      } catch (err) {
        console.warn(`[courseService] getCourseById(${id}) fell back to mock:`, err);
      }
    }

    // Mock fallback — try exact string id match first, then numeric index
    await delay(200);
    const byId = mockCourses.find(c => c.id === id);
    if (byId) return byId;

    // If id is a number, try treating it as a 1-based index into mock courses
    if (!isNaN(numId) && numId >= 1 && numId <= mockCourses.length) {
      return mockCourses[numId - 1];
    }

    return null;
  },

  async searchCourses(query: string): Promise<Course[]> {
    try {
      const data = await get<BackendCourseList[]>(
        `/api/courses?search=${encodeURIComponent(query)}`
      );
      return data.map(mapListItem);
    } catch (err) {
      console.warn('[courseService] searchCourses fell back to mock:', err);
      await delay(150);
      const q = query.toLowerCase();
      return mockCourses.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.code.toLowerCase().includes(q) ||
        c.program.toLowerCase().includes(q) ||
        c.units.some(u =>
          u.title.toLowerCase().includes(q) ||
          u.topics.some(t => t.title.toLowerCase().includes(q))
        )
      );
    }
  },

  async getRecentCourses(limit = 5): Promise<Course[]> {
    const all = await this.getAllCourses();
    return all.slice(0, limit);
  },

  async getRegulations(): Promise<string[]> {
    try {
      const data = await get<{ code: string }[]>('/api/regulations');
      return data.map(item => item.code).filter(Boolean);
    } catch (err) {
      console.warn('[courseService] getRegulations failed:', err);
      return [];
    }
  },

};
