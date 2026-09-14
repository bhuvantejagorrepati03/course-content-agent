import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, MessageCircle, Download, BookOpen, ChevronDown, ChevronUp, Clock, Hash, Target, BookMarked, BarChart2 } from 'lucide-react';
import type { Course, COPOMapping } from '../types';
import { courseService } from '../services/courseService';
import { API_BASE } from '../services/api';
import { useToast } from '../context/ToastContext';

const TABS = ['Overview', 'Units & Topics', 'Course Outcomes', 'Textbooks', 'CO-PO Mapping'] as const;
type Tab = typeof TABS[number];

const mappingColors: Record<number, string> = {
  0: 'bg-gray-50 text-gray-400',
  1: 'bg-blue-50 text-blue-500',
  2: 'bg-blue-100 text-blue-700',
  3: 'bg-blue-600 text-white',
};

export default function CourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState<Course | null>(null);
  const [mappings, setMappings] = useState<COPOMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('Overview');
  const { showToast } = useToast();
  const targetUnit = Number(searchParams.get('unit')) || undefined;
  const targetTopic = searchParams.get('topic') || undefined;

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setCourse(null);
    setMappings([]);
    courseService.getCourseById(id).then(async c => {
      setCourse(c);
      setLoading(false);
      if (c && targetUnit) setTab('Units & Topics');
      // Also fetch CO-PO mapping from the dedicated endpoint
      if (c) {
        try {
          const res = await fetch(`${API_BASE}/api/mapping/${c.id}`);
          if (res.ok) {
            const json = await res.json();
            if (json.success && json.data?.matrix) {
              // Convert backend matrix format to frontend COPOMapping[]
              const converted: COPOMapping[] = json.data.matrix.map((row: { co: string; values: Record<string, number> }) => ({
                courseOutcomeId: row.co,
                mappings: row.values,
              }));
              setMappings(converted);
            }
          }
        } catch {
          // Mapping not critical — silently ignore
        }
      }
    });
  }, [id, targetUnit]);

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-500 text-sm">Loading course...</p>
      </div>
    </div>
  );

  if (!course) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <BookOpen size={48} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-600 font-medium">Course not found</p>
        <button onClick={() => navigate('/courses')} className="mt-3 text-blue-600 text-sm hover:underline">
          Back to Courses
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-100 sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 py-3 text-sm text-gray-500">
            <button onClick={() => navigate('/courses')} className="flex items-center gap-1 hover:text-blue-600 transition-colors">
              <ArrowLeft size={14} /> Courses
            </button>
            <span>/</span>
            <span className="text-gray-700 font-medium">{course.name}</span>
          </div>

          {/* Course header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{course.name}</h1>
                <span className="text-xs font-medium px-2 py-0.5 bg-green-100 text-green-700 rounded-full">Indexed</span>
              </div>
              <p className="text-sm text-gray-500">
                {course.code} · {course.program} · {course.year} · {course.regulation} · {course.credits} Credits
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => { showToast({ type: 'info', title: 'Summary exported', message: 'PDF download started' }); }}
                className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <Download size={14} /> Export
              </button>
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-sm"
              >
                <MessageCircle size={14} /> Ask AI
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-0 overflow-x-auto -mb-px">
            {TABS.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`shrink-0 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap
                  ${tab === t ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
        {tab === 'Overview' && <OverviewTab course={course} />}
        {tab === 'Units & Topics' && <UnitsTab course={course} targetUnit={targetUnit} targetTopic={targetTopic} />}
        {tab === 'Course Outcomes' && <COTab course={course} />}
        {tab === 'Textbooks' && <TextbooksTab course={course} />}
        {tab === 'CO-PO Mapping' && <MappingTab course={course} mappings={mappings} />}
      </div>
    </div>
  );
}

// ── Overview ──────────────────────────────────────────────────
function OverviewTab({ course }: { course: Course }) {
  const totalTopics = course.units.reduce((s, u) => s + u.topics.length, 0);
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {/* Description */}
      <div className="md:col-span-2 space-y-4">
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><BookOpen size={16} className="text-blue-500" /> Course Description</h2>
          <p className="text-sm text-gray-600 leading-relaxed">{course.description}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-800 mb-3">Prerequisites</h2>
          <div className="flex flex-wrap gap-2">
            {course.prerequisites.map(p => (
              <span key={p} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-100">{p}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Stats sidebar */}
      <div className="space-y-3">
        {[
          { label: 'Credits', value: course.credits, icon: <Hash size={16} className="text-blue-500" /> },
          { label: 'Total Hours', value: course.totalHours, icon: <Clock size={16} className="text-blue-500" /> },
          { label: 'Units', value: course.units.length, icon: <BarChart2 size={16} className="text-blue-500" /> },
          { label: 'Topics', value: totalTopics, icon: <Target size={16} className="text-blue-500" /> },
          { label: 'Course Outcomes', value: course.courseOutcomes.length, icon: <BookMarked size={16} className="text-blue-500" /> },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              {s.icon}{s.label}
            </div>
            <span className="text-xl font-bold text-gray-900">{s.value}</span>
          </div>
        ))}
        <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl p-4 text-white">
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-200 mb-1">Regulation</p>
          <p className="text-2xl font-bold">{course.regulation}</p>
          <p className="text-sm text-blue-200 mt-1">{course.program} · {course.year}</p>
        </div>
      </div>
    </div>
  );
}

// ── Units & Topics ────────────────────────────────────────────
function UnitsTab({ course, targetUnit, targetTopic }: { course: Course; targetUnit?: number; targetTopic?: string }) {
  // Open the first unit by default (use unit number as key, robust across data sources)
  const [openNums, setOpenNums] = useState<number[]>(
    targetUnit ? [targetUnit] : course.units.length > 0 ? [course.units[0].number] : []
  );
  const [highlightedTopic, setHighlightedTopic] = useState<string | undefined>();
  const toggle = (num: number) =>
    setOpenNums(prev => prev.includes(num) ? prev.filter(x => x !== num) : [...prev, num]);

  useEffect(() => {
    if (!targetUnit) return;
    setOpenNums(prev => prev.includes(targetUnit) ? prev : [...prev, targetUnit]);
    const targetId = targetTopic ? `topic-${targetTopic}` : `unit-${targetUnit}`;
    const timer = window.setTimeout(() => {
      const element = document.getElementById(targetId);
      element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (targetTopic && element) {
        setHighlightedTopic(targetTopic);
        window.setTimeout(() => setHighlightedTopic(undefined), 2200);
      }
    }, 80);
    return () => window.clearTimeout(timer);
  }, [targetUnit, targetTopic, course.id]);

  if (course.units.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
        <BookOpen size={36} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500">No units available for this course.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {course.units.map(unit => {
        const isOpen = openNums.includes(unit.number);
        return (
          <div id={`unit-${unit.number}`} key={unit.id} className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <button
              onClick={() => toggle(unit.number)}
              className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white text-sm font-bold shrink-0">
                  {unit.number}
                </span>
                <div>
                  <p className="font-semibold text-gray-900 text-sm">
                    UNIT {unit.number} — {unit.title || `Unit ${unit.number}`}
                  </p>
                  <div className="flex flex-wrap items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock size={11} />{unit.hours} hrs
                    </span>
                    <span className="text-xs text-gray-500">{unit.topics.length} topics</span>
                    {unit.coMapping.map(co => (
                      <span key={co} className="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded-full font-medium">{co}</span>
                    ))}
                  </div>
                </div>
              </div>
              {isOpen
                ? <ChevronUp size={16} className="text-gray-400 shrink-0" />
                : <ChevronDown size={16} className="text-gray-400 shrink-0" />
              }
            </button>

            {isOpen && (
              <div className="px-5 pb-4 border-t border-gray-50">
                {unit.description && (
                  <p className="text-sm text-gray-500 py-3 italic">{unit.description}</p>
                )}
                {unit.topics.length === 0 ? (
                  <p className="text-sm text-gray-400 py-3">No topic details available.</p>
                ) : (
                  <ul className="space-y-2 mt-2">
                    {unit.topics.map((topic, i) => (
                      <li id={`topic-${topic.id}`} key={topic.id} className={`flex items-start gap-3 rounded-lg px-2 py-1 transition-colors ${highlightedTopic === topic.id ? 'bg-amber-100 ring-2 ring-amber-300' : ''}`}>
                        <span className="shrink-0 w-5 h-5 rounded-full bg-blue-50 border border-blue-100 text-xs text-blue-600 font-medium flex items-center justify-center mt-0.5">
                          {i + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-800">{topic.title}</p>
                          {topic.subtopics && topic.subtopics.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-1">
                              {topic.subtopics.map(s => (
                                <span key={s} className="text-xs px-2 py-0.5 bg-gray-50 border border-gray-100 text-gray-500 rounded-full">{s}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Course Outcomes ───────────────────────────────────────────
function COTab({ course }: { course: Course }) {
  const bloomColors: Record<string, string> = {
    'Understand': 'bg-blue-50 text-blue-600',
    'Apply': 'bg-green-50 text-green-600',
    'Analyze': 'bg-amber-50 text-amber-600',
    'Evaluate': 'bg-purple-50 text-purple-600',
    'Create': 'bg-rose-50 text-rose-600',
  };
  return (
    <div className="space-y-3">
      {course.courseOutcomes.map((co, i) => (
        <div key={co.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-start gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600 text-white font-bold text-lg shrink-0">
            {i + 1}
          </div>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="font-bold text-blue-700 text-sm">{co.code}</span>
              {co.bloomLevel && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${bloomColors[co.bloomLevel] ?? 'bg-gray-50 text-gray-500'}`}>
                  {co.bloomLevel}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{co.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Textbooks ─────────────────────────────────────────────────
function TextbooksTab({ course }: { course: Course }) {
  return (
    <div className="space-y-5">
      <section>
        <h2 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3">Prescribed Textbooks</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {course.textbooks.map((tb, i) => (
            <div key={tb.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4">
              <div className="shrink-0 w-10 h-14 bg-gradient-to-b from-blue-500 to-indigo-700 rounded-lg flex items-center justify-center text-white text-lg font-bold">
                {i + 1}
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm leading-snug">{tb.title}</p>
                <p className="text-xs text-gray-500 mt-1">{tb.author}</p>
                <p className="text-xs text-gray-400 mt-0.5">{tb.edition} · {tb.publisher}</p>
                {tb.year && <p className="text-xs text-gray-400">{tb.year}</p>}
              </div>
            </div>
          ))}
        </div>
      </section>

      {course.referenceBooks.length > 0 && (
        <section>
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-3">Reference Books</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {course.referenceBooks.map((rb, i) => (
              <div key={rb.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex gap-4">
                <div className="shrink-0 w-10 h-14 bg-gradient-to-b from-gray-400 to-gray-600 rounded-lg flex items-center justify-center text-white text-lg font-bold">
                  {i + 1}
                </div>
                <div>
                  <p className="font-semibold text-gray-900 text-sm leading-snug">{rb.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{rb.author}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{rb.edition} · {rb.publisher}</p>
                  {rb.year && <p className="text-xs text-gray-400">{rb.year}</p>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

// ── CO-PO Mapping ─────────────────────────────────────────────
function MappingTab({ course, mappings }: { course: Course; mappings: COPOMapping[] }) {
  // Use fetched mappings if available, otherwise fall back to course.mappings
  const effectiveMappings = mappings.length > 0 ? mappings : course.mappings;
  const poKeys = ['PO1', 'PO2', 'PO3', 'PO4', 'PO5', 'PO6', 'PSO1', 'PSO2'];

  if (effectiveMappings.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
        <BarChart2 size={36} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500 font-medium">CO-PO mapping not available for this course.</p>
      </div>
    );
  }

  // Determine which columns actually have data
  const usedColumns = poKeys.filter(k => effectiveMappings.some(m => m.mappings[k] !== undefined));
  const columns = usedColumns.length > 0 ? usedColumns : poKeys;

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-50">
          <h2 className="font-semibold text-gray-800">CO-PO Mapping Matrix</h2>
          <p className="text-xs text-gray-500 mt-0.5">Correlation level: 3 = High, 2 = Medium, 1 = Low, 0 = None</p>
          {!columns.some(column => column.startsWith('PSO')) && (
            <p className="text-xs text-amber-600 mt-1">No course-specific CO-PSO mapping is present in the imported syllabus.</p>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left font-semibold text-gray-600 w-16">CO</th>
                {columns.map(k => (
                  <th key={k} className="px-3 py-3 text-center font-semibold text-gray-600 min-w-[56px]">{k}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {effectiveMappings.map((m, i) => (
                <tr key={m.courseOutcomeId} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                  <td className="px-4 py-3 font-bold text-blue-700">{m.courseOutcomeId}</td>
                  {columns.map(k => {
                    const val = m.mappings[k] ?? 0;
                    return (
                      <td key={k} className="px-3 py-3 text-center">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-bold text-sm ${mappingColors[val] ?? mappingColors[0]}`}>
                          {val}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {[
          { val: 3, label: 'High', color: 'bg-blue-600 text-white' },
          { val: 2, label: 'Medium', color: 'bg-blue-100 text-blue-700' },
          { val: 1, label: 'Low', color: 'bg-blue-50 text-blue-500' },
          { val: 0, label: 'None', color: 'bg-gray-50 text-gray-400' },
        ].map(l => (
          <div key={l.val} className="flex items-center gap-2">
            <span className={`w-7 h-7 rounded-lg font-bold text-sm flex items-center justify-center ${l.color}`}>{l.val}</span>
            <span className="text-sm text-gray-600">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
