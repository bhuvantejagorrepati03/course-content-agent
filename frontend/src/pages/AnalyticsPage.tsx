import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { BookOpen, FileText, Hash, Target } from 'lucide-react';
import type { AnalyticsData } from '../types';
import { analyticsService } from '../services/analyticsService';
import { mockAnalyticsData } from '../data/mockData';

const PIE_COLORS = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe'];

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>(mockAnalyticsData);

  useEffect(() => {
    analyticsService.getAnalytics().then(setAnalyticsData);
  }, []);

  const d = analyticsData;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-sm text-gray-500 mt-1">Overview of indexed courses, topics, and outcomes.</p>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Courses', value: d.totalCourses, icon: <BookOpen size={20} />, color: 'text-blue-600 bg-blue-50' },
            { label: 'Syllabus Docs', value: d.totalDocuments, icon: <FileText size={20} />, color: 'text-indigo-600 bg-indigo-50' },
            { label: 'Topics Indexed', value: d.totalTopics.toLocaleString(), icon: <Hash size={20} />, color: 'text-purple-600 bg-purple-50' },
            { label: 'Course Outcomes', value: d.totalCOs, icon: <Target size={20} />, color: 'text-green-600 bg-green-50' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${s.color}`}>{s.icon}</div>
              <p className="text-2xl font-bold text-gray-900">{s.value}</p>
              <p className="text-sm text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Courses by program */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Courses by Program</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={d.coursesByProgram} dataKey="count" nameKey="program" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                  {d.coursesByProgram.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Topics per course */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Topics per Course</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={d.topicsPerCourse} margin={{ top: 0, right: 10, bottom: 0, left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="course" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                <Bar dataKey="topics" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CO Distribution */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-800 mb-4">CO Distribution by Bloom's Level</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={d.coDistribution} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis dataKey="level" type="category" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} width={80} />
              <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Additional stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { label: 'Units Processed', value: d.unitsProcessed, desc: 'Across all courses' },
            { label: 'Textbooks Extracted', value: d.textbooksExtracted, desc: 'Prescribed & reference' },
            { label: 'Avg Topics/Course', value: Math.round(d.totalTopics / d.totalCourses), desc: 'Per indexed course' },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 text-center">
              <p className="text-3xl font-bold text-blue-700">{s.value}</p>
              <p className="font-medium text-gray-700 mt-1">{s.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
