import { useEffect, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { courseService } from '../services/courseService';
import { API_BASE } from '../services/api';
import type { Course, COPOMapping } from '../types';

const mappingColors: Record<number, string> = {
  0: 'bg-gray-50 text-gray-300 border border-gray-100',
  1: 'bg-blue-50 text-blue-500 border border-blue-100',
  2: 'bg-blue-100 text-blue-700 border border-blue-200',
  3: 'bg-blue-600 text-white border border-blue-600',
};

const poLabels: Record<string, string> = {
  PO1: 'Engineering Knowledge',
  PO2: 'Problem Analysis',
  PO3: 'Design Solutions',
  PO4: 'Investigation',
  PO5: 'Modern Tools',
  PO6: 'Engineer & Society',
  PSO1: 'Domain Specific 1',
  PSO2: 'Domain Specific 2',
};

export default function MappingPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState('');
  const [mappings, setMappings] = useState<COPOMapping[]>([]);
  const [mappingLoaded, setMappingLoaded] = useState(false);
  const [courseDetails, setCourseDetails] = useState<Course | null>(null);
  const course = courses.find(c => c.id === courseId) ?? courses[0];
  const displayCourse = courseDetails?.id === course?.id ? courseDetails : course;

  useEffect(() => {
    courseService.getAllCourses().then(data => {
      setCourses(data);
      if (data.length > 0) setCourseId(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!course) return;
    setCourseDetails(null);
    courseService.getCourseById(course.id).then(detail => {
      if (detail?.id === course.id) setCourseDetails(detail);
    });
  }, [course?.id]);

  useEffect(() => {
    if (!course) return;
    setMappings([]);
    setMappingLoaded(false);
    fetch(`${API_BASE}/api/mapping/${course.id}`)
      .then(response => response.ok ? response.json() : null)
      .then(json => {
        const rows = json?.data?.matrix as { co: string; values: Record<string, number> }[] | undefined;
        setMappings(rows?.map(row => ({ courseOutcomeId: row.co, mappings: row.values })) ?? []);
        setMappingLoaded(true);
      })
      .catch(() => {
        setMappings([]);
        setMappingLoaded(true);
      });
  }, [course]);

  if (!displayCourse) return <div className="min-h-screen bg-gray-50 p-8 text-gray-500">Loading mappings...</div>;

  const effectiveMappings = mappings.length > 0 ? mappings : displayCourse.mappings;
  const poKeys = [...new Set(effectiveMappings.flatMap(mapping => Object.keys(mapping.mappings)))].sort((a, b) => {
    const aNum = Number(a.replace(/\D/g, '')) || 0;
    const bNum = Number(b.replace(/\D/g, '')) || 0;
    return a.replace(/\d/g, '').localeCompare(b.replace(/\d/g, '')) || aNum - bNum;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">CO / PO / PSO Mapping</h1>
        <p className="text-sm text-gray-500 mt-1">Explore course outcome alignment with program outcomes.</p>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Course selector */}
        <div className="flex items-center gap-3">
          <label className="text-sm font-semibold text-gray-600">Course:</label>
          <div className="relative">
            <select
              value={courseId}
              onChange={e => setCourseId(e.target.value)}
              className="appearance-none bg-white border border-gray-200 rounded-lg pl-3 pr-8 py-2 text-sm font-medium text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer"
            >
              {courses.map(c => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
            </select>
            <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          </div>
        </div>

        {/* Matrix */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-semibold text-gray-800">{displayCourse.name} — CO-PO Mapping Matrix</h2>
              <p className="text-xs text-gray-400 mt-0.5">{displayCourse.code} · {displayCourse.program} · {displayCourse.regulation}</p>
              {mappingLoaded && effectiveMappings.length === 0 && <p className="text-xs text-amber-600 mt-1">No course-specific CO-PSO mapping is present in the imported syllabus.</p>}
            </div>
            <div className="flex gap-3 flex-wrap">
              {[
                { val: 3, label: 'High', color: 'bg-blue-600 text-white' },
                { val: 2, label: 'Medium', color: 'bg-blue-100 text-blue-700' },
                { val: 1, label: 'Low', color: 'bg-blue-50 text-blue-500' },
                { val: 0, label: 'None', color: 'bg-gray-50 text-gray-400 border border-gray-100' },
              ].map(l => (
                <div key={l.val} className="flex items-center gap-1.5">
                  <span className={`w-6 h-6 rounded font-bold text-xs flex items-center justify-center ${l.color}`}>{l.val}</span>
                  <span className="text-xs text-gray-500">{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left font-semibold text-gray-600 sticky left-0 bg-gray-50 z-10 min-w-[80px]">
                    CO / PO
                  </th>
                  {poKeys.map(k => (
                    <th key={k} className="px-2 py-3 text-center min-w-[64px]">
                      <div className="font-bold text-gray-700">{k}</div>
                      <div className="text-xs font-normal text-gray-400 mt-0.5 leading-tight max-w-[60px] mx-auto">{poLabels[k]}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {effectiveMappings.map((m, i) => {
                  const co = displayCourse.courseOutcomes.find(c => c.code === m.courseOutcomeId);
                  return (
                    <tr key={m.courseOutcomeId} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/40'}>
                      <td className="px-4 py-3 sticky left-0 bg-inherit z-10">
                        <div className="font-bold text-blue-700">{m.courseOutcomeId}</div>
                        {co && <div className="text-xs text-gray-400 mt-0.5 max-w-[120px] leading-tight">{co.bloomLevel}</div>}
                      </td>
                      {poKeys.map(k => {
                        const val = m.mappings[k] ?? 0;
                        return (
                          <td key={k} className="px-2 py-3 text-center">
                            <span className={`inline-flex items-center justify-center w-9 h-9 rounded-lg font-bold text-sm ${mappingColors[val] ?? mappingColors[0]}`}>
                              {val}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* CO Descriptions */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-4">Course Outcomes</h3>
          <div className="space-y-2">
            {displayCourse.courseOutcomes.map(co => (
              <div key={co.id} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
                <span className="shrink-0 w-10 text-sm font-bold text-blue-700 pt-0.5">{co.code}</span>
                <span className="text-sm text-gray-600 leading-relaxed">{co.description}</span>
                {co.bloomLevel && (
                  <span className="shrink-0 text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">{co.bloomLevel}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
