import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, BookOpen, Users, Clock, ChevronRight, MessageCircle, Filter } from 'lucide-react';
import type { Course } from '../types';
import { courseService } from '../services/courseService';
import { useToast } from '../context/ToastContext';

const statusColors = {
  indexed: 'bg-green-100 text-green-700',
  processing: 'bg-amber-100 text-amber-700',
  pending: 'bg-gray-100 text-gray-600',
};

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [filtered, setFiltered] = useState<Course[]>([]);
  const [search, setSearch] = useState('');
  const [filterProgram, setFilterProgram] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterReg, setFilterReg] = useState('');
  const [loading, setLoading] = useState(true);
  const [regulations, setRegulations] = useState<string[]>([]);
  const navigate = useNavigate();
  const { showToast } = useToast();

  useEffect(() => {
    Promise.all([courseService.getAllCourses(), courseService.getRegulations()]).then(([data, availableRegulations]) => {
      setCourses(data);
      setFiltered(data);
      setRegulations(availableRegulations);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    let result = courses;
    if (search) result = result.filter(c =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.code.toLowerCase().includes(search.toLowerCase())
    );
    if (filterProgram) result = result.filter(c => c.program === filterProgram);
    if (filterYear) result = result.filter(c => c.year === filterYear);
    if (filterReg) result = result.filter(c => c.regulation === filterReg);
    setFiltered(result);
  }, [search, filterProgram, filterYear, filterReg, courses]);

  const programs = [...new Set(courses.map(c => c.program))].sort();
  const yearOrder = ['I Year', 'II Year', 'III Year', 'IV Year'];
  const years = yearOrder.filter(year => courses.some(c => c.year === year));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Courses</h1>
        <p className="text-sm text-gray-500 mt-1">Browse and explore structured university course content.</p>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search courses..."
              className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            <div className="relative">
              <Filter size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <select value={filterProgram} onChange={e => setFilterProgram(e.target.value)}
                className="pl-7 pr-3 py-2.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer">
                <option value="">All Programs</option>
                {programs.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <select value={filterYear} onChange={e => setFilterYear(e.target.value)}
              className="px-3 py-2.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer">
              <option value="">All Years</option>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
            <select value={filterReg} onChange={e => setFilterReg(e.target.value)}
              className="px-3 py-2.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer">
              <option value="">All Regulations</option>
              {regulations.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        </div>

        {/* Results count */}
        <p className="text-sm text-gray-500 mb-4">{filtered.length} course{filtered.length !== 1 ? 's' : ''} found</p>

        {/* Courses grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
                <div className="h-3 bg-gray-100 rounded w-1/2 mb-4" />
                <div className="h-3 bg-gray-100 rounded w-full mb-2" />
                <div className="h-3 bg-gray-100 rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-gray-100">
            <BookOpen size={40} className="mx-auto text-gray-300 mb-3" />
            <p className="text-gray-500 font-medium">No courses found</p>
            <p className="text-sm text-gray-400 mt-1">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map(course => (
              <CourseCard
                key={course.id}
                course={course}
                onView={() => navigate(`/courses/${course.id}`)}
                onAsk={() => {
                  showToast({ type: 'info', title: `Switched to ${course.name}`, message: 'Ask AI loaded' });
                  navigate('/');
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CourseCard({ course, onView, onAsk }: { course: Course; onView: () => void; onAsk: () => void }) {
  const totalTopics = course.topicCount ?? course.units.reduce((s, u) => s + u.topics.length, 0);
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group">
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0 pr-2">
            <h3 className="font-bold text-gray-900 group-hover:text-blue-700 transition-colors leading-tight">{course.name}</h3>
            <p className="text-blue-600 font-mono text-xs mt-0.5">{course.code}</p>
          </div>
          <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${statusColors[course.status]}`}>
            {course.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-4">
          <div className="flex items-center gap-1.5">
            <Users size={12} className="text-blue-400" />
            <span>{course.program}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock size={12} className="text-blue-400" />
            <span>{course.year}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen size={12} className="text-blue-400" />
            <span>{course.unitCount ?? course.units.length} Units · {totalTopics} Topics</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-medium text-blue-500">{course.regulation}</span>
            <span>· {course.credits} Cr</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full font-medium">
            {course.courseOutcomes.length} COs
          </span>
          <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full font-medium">
            {course.totalHours} hrs
          </span>
        </div>
      </div>

      <div className="border-t border-gray-50 px-5 py-3 flex gap-2">
        <button
          onClick={onView}
          className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg py-2 transition-colors"
        >
          View Course <ChevronRight size={13} />
        </button>
        <button
          onClick={onAsk}
          className="flex items-center justify-center gap-1.5 text-xs font-semibold text-gray-600 bg-gray-50 hover:bg-gray-100 rounded-lg py-2 px-3 transition-colors"
        >
          <MessageCircle size={13} />
          Ask AI
        </button>
      </div>
    </div>
  );
}
