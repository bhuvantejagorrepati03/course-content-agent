import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, FileText, Hash, Target, Upload, MessageCircle,
  LayoutGrid, Map, Search, ChevronRight, TrendingUp, Clock,
  Bell, CheckCircle, GraduationCap,
} from 'lucide-react';
import type { Course } from '../types';
import { courseService } from '../services/courseService';
import { analyticsService } from '../services/analyticsService';
import type { AnalyticsData } from '../types';
import { useRole } from '../context/RoleContext';
import RoleSwitcher from '../components/RoleSwitcher';
// ── Stat Card ─────────────────────────────────────────────────
function StatCard({ label, value, icon, color, change }: {
  label: string; value: string | number; icon: React.ReactNode;
  color: string; change?: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
          {icon}
        </div>
        {change && (
          <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
            <TrendingUp size={11} /> {change}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

// ── Quick Action Card ─────────────────────────────────────────
function QuickAction({ icon, label, desc, color, onClick }: {
  icon: React.ReactNode; label: string; desc: string;
  color: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-left hover:shadow-md hover:-translate-y-0.5 transition-all w-full"
    >
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 ${color} group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <p className="font-semibold text-gray-900 text-sm">{label}</p>
      <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
    </button>
  );
}

// ── Course Row ────────────────────────────────────────────────
function CourseRow({ course, onClick }: { course: Course; onClick: () => void }) {
  const totalTopics = course.topicCount ?? course.units.reduce((s, u) => s + u.topics.length, 0);
  return (
    <tr
      className="hover:bg-blue-50/50 cursor-pointer transition-colors group"
      onClick={onClick}
    >
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            {course.code.slice(0, 2)}
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm group-hover:text-blue-700 transition-colors">
              {course.name}
            </p>
            <p className="text-xs text-blue-500 font-mono">{course.code}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{course.program}</td>
      <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">{course.year}</td>
      <td className="px-4 py-3 hidden md:table-cell">
        <span className="text-xs font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
          {course.regulation}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 hidden lg:table-cell">{course.unitCount ?? course.units.length} units · {totalTopics} topics</td>
      <td className="px-4 py-3">
        <span className="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full w-fit">
          <CheckCircle size={11} /> Indexed
        </span>
      </td>
      <td className="px-4 py-3">
        <ChevronRight size={15} className="text-gray-400 group-hover:text-blue-600 transition-colors" />
      </td>
    </tr>
  );
}

// ── Main Dashboard ────────────────────────────────────────────
export default function DashboardPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Course[]>([]);
  const [searching, setSearching] = useState(false);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [courseCount, setCourseCount] = useState(0);
  const navigate = useNavigate();
  const { isFaculty } = useRole();

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  useEffect(() => {
    Promise.all([courseService.getAllCourses(), analyticsService.getAnalytics()]).then(([allCourses, stats]) => {
      setCourses(allCourses.slice(0, 5));
      setCourseCount(allCourses.length);
      setAnalytics(stats);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    const t = setTimeout(() => {
      courseService.searchCourses(searchQuery)
        .then(r => {
          setSearchResults(r);
          setSearching(false);
        })
        .catch(() => {
          setSearchResults([]);
          setSearching(false);
        });
    }, 300);

    return () => clearTimeout(t);
  }, [searchQuery]);

  const displayCourses = searchQuery.trim() ? searchResults : courses;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Hero Header ──────────────────────────────────── */}
      <div className="bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-900 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-400/30 flex items-center justify-center">
                <BookOpen size={18} className="text-blue-300" />
              </div>
              <div>
                <p className="text-xs text-blue-300 font-medium uppercase tracking-widest">CourseAI</p>
                <p className="text-xs text-blue-400/70">Course Content Agent</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                className="relative p-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors"
                aria-label="Notifications"
              >
                <Bell size={17} className="text-white/80" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-400 rounded-full" />
              </button>
              {/* Role switcher — replaces static "Faculty" */}
              <RoleSwitcher />
            </div>
          </div>

          {/* Greeting */}
          <div className="mb-7">
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">
              {greeting} 👋
            </h1>
            <p className="text-blue-300 text-sm sm:text-base">
              {isFaculty
                ? 'Explore and manage your university course content.'
                : 'Explore your university course content and learn with AI.'}
            </p>
            {/* Student mode notice */}
            {!isFaculty && (
              <div className="inline-flex items-center gap-2 mt-3 px-3 py-1.5 bg-green-500/20 border border-green-400/30 rounded-full">
                <GraduationCap size={14} className="text-green-300" />
                <span className="text-xs text-green-200 font-medium">Student mode — read-only access</span>
              </div>
            )}
          </div>

          {/* Search bar */}
          <div className="relative max-w-2xl">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search courses, topics, units, textbooks..."
              className="w-full pl-11 pr-4 py-3.5 rounded-2xl bg-white text-gray-800 placeholder-gray-400 text-sm shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="Search courses and topics"
            />
            {searching && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-8">
            {[
              { label: 'Total Courses', value: courseCount, icon: <BookOpen size={16} />, subtitle: 'Indexed' },
              { label: 'Syllabus Documents', value: analytics?.totalDocuments ?? 0, icon: <FileText size={16} />, subtitle: 'Uploaded' },
              { label: 'Topics Indexed', value: analytics?.totalTopics ?? 0, icon: <Hash size={16} />, subtitle: 'Extracted' },
              { label: 'Course Outcomes', value: analytics?.totalCOs ?? 0, icon: <Target size={16} />, subtitle: 'Mapped' },
            ].map(s => (
              <div key={s.label} className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/10">
                <div className="flex items-center gap-2 mb-2 text-blue-300">
                  {s.icon}
                  <span className="text-xs text-blue-300/70">{s.subtitle}</span>
                </div>
                <p className="text-2xl font-bold text-white">{s.value}</p>
                <p className="text-xs text-blue-300/80 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Body ─────────────────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-7 space-y-8">

        {/* Quick Actions */}
        <section>
          <h2 className="text-base font-bold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {isFaculty && (
              <QuickAction
                icon={<Upload size={20} className="text-blue-600" />}
                label="Upload Syllabus"
                desc="Process a new PDF"
                color="bg-blue-50"
                onClick={() => navigate('/syllabus')}
              />
            )}
            <QuickAction
              icon={<MessageCircle size={20} className="text-indigo-600" />}
              label="Ask AI Assistant"
              desc="Chat about courses"
              color="bg-indigo-50"
              onClick={() => navigate('/assistant')}
            />
            <QuickAction
              icon={<LayoutGrid size={20} className="text-purple-600" />}
              label="Browse Courses"
              desc="View all courses"
              color="bg-purple-50"
              onClick={() => navigate('/courses')}
            />
            <QuickAction
              icon={<Map size={20} className="text-green-600" />}
              label="CO-PO Mapping"
              desc="View outcome mapping"
              color="bg-green-50"
              onClick={() => navigate('/mapping')}
            />
          </div>
        </section>

        {/* Stat cards */}
        <section>
          <h2 className="text-base font-bold text-gray-800 mb-4">System Overview</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Courses" value={courseCount} icon={<BookOpen size={20} className="text-blue-600" />} color="bg-blue-50" />
            <StatCard label="Syllabus Documents" value={analytics?.totalDocuments ?? 0} icon={<FileText size={20} className="text-indigo-600" />} color="bg-indigo-50" />
            <StatCard label="Topics Indexed" value={(analytics?.totalTopics ?? 0).toLocaleString()} icon={<Hash size={20} className="text-purple-600" />} color="bg-purple-50" />
            <StatCard label="Course Outcomes" value={analytics?.totalCOs ?? 0} icon={<Target size={20} className="text-green-600" />} color="bg-green-50" />
          </div>
        </section>

        {/* Recently Added Courses */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-gray-800">
              {searchQuery.trim() ? `Search Results (${displayCourses.length})` : 'Recently Added Courses'}
            </h2>
            <button
              onClick={() => navigate('/courses')}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              View all <ChevronRight size={14} />
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-6 space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex items-center gap-4 animate-pulse">
                    <div className="w-9 h-9 bg-gray-100 rounded-lg shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3.5 bg-gray-100 rounded w-1/3" />
                      <div className="h-3 bg-gray-50 rounded w-1/5" />
                    </div>
                  </div>
                ))}
              </div>
            ) : displayCourses.length === 0 ? (
              <div className="py-14 text-center">
                <BookOpen size={36} className="mx-auto text-gray-300 mb-3" />
                <p className="text-gray-500 font-medium">No courses found</p>
                {searchQuery && <p className="text-sm text-gray-400 mt-1">Try a different search term</p>}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50/70">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Course</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden sm:table-cell">Program</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Year</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Regulation</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">Content</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {displayCourses.map(course => (
                      <CourseRow
                        key={course.id}
                        course={course}
                        onClick={() => navigate(`/courses/${course.id}`)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* Bottom CTA strip — faculty only */}
        {isFaculty && (
        <section className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-white text-center sm:text-left">
            <p className="font-bold text-lg">Have a new syllabus?</p>
            <p className="text-blue-200 text-sm mt-0.5">Upload it and our AI will extract, structure, and index it automatically.</p>
          </div>
          <div className="flex gap-3 shrink-0">
            <button
              onClick={() => navigate('/syllabus')}
              className="flex items-center gap-2 px-5 py-2.5 bg-white text-blue-700 font-semibold rounded-xl hover:bg-blue-50 transition-colors shadow-sm text-sm"
            >
              <Upload size={15} /> Upload Syllabus
            </button>
            <button
              onClick={() => navigate('/assistant')}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-500/30 border border-white/20 text-white font-semibold rounded-xl hover:bg-blue-500/40 transition-colors text-sm"
            >
              <MessageCircle size={15} /> Ask AI
            </button>
          </div>
        </section>
        )}

        {/* Recent activity */}
        <section>
          <h2 className="text-base font-bold text-gray-800 mb-4">Recent Activity</h2>
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
            {[
              { icon: <CheckCircle size={15} className="text-green-500" />, text: 'DataStructures_R23.pdf indexed successfully', time: '2 hours ago', color: 'bg-green-50' },
              { icon: <Upload size={15} className="text-blue-500" />, text: 'CN_R23.pdf uploaded and processed', time: '1 day ago', color: 'bg-blue-50' },
              { icon: <Map size={15} className="text-purple-500" />, text: 'CO-PO mapping updated for CS401', time: '2 days ago', color: 'bg-purple-50' },
              { icon: <Clock size={15} className="text-amber-500" />, text: 'OS_R23.pdf processing completed', time: '3 days ago', color: 'bg-amber-50' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-3.5">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${item.color}`}>
                  {item.icon}
                </div>
                <p className="flex-1 text-sm text-gray-700">{item.text}</p>
                <span className="text-xs text-gray-400 shrink-0">{item.time}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
