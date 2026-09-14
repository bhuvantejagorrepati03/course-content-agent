/**
 * Analytics Service
 * ---------------------------------------------------------------------------
 * Fetches aggregate stats. Falls back to mock data if backend is unavailable.
 * ---------------------------------------------------------------------------
 */
import type { AnalyticsData } from '../types';
import { mockAnalyticsData } from '../data/mockData';
import { apiFetch, API_BASE } from './api';

let _backendAvailable: boolean | null = null;

async function isBackendAvailable(): Promise<boolean> {
  if (_backendAvailable !== null) return _backendAvailable;
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(1500) });
    _backendAvailable = res.ok;
  } catch {
    _backendAvailable = false;
  }
  return _backendAvailable;
}

interface BackendAnalytics {
  total_courses: number;
  total_documents: number;
  total_units: number;
  total_topics: number;
  total_outcomes: number;
  total_textbooks: number;
  courses_by_program: { program: string; count: number }[];
  topics_per_course: { course: string; topics: number }[];
  co_distribution: { level: string; count: number }[];
}

export const analyticsService = {
  async getAnalytics(): Promise<AnalyticsData> {
    if (await isBackendAvailable()) {
      try {
        const d = await apiFetch<BackendAnalytics>('/api/analytics');
        return {
          totalCourses: d.total_courses,
          totalDocuments: d.total_documents,
          totalTopics: d.total_topics,
          totalCOs: d.total_outcomes,
          unitsProcessed: d.total_units,
          textbooksExtracted: d.total_textbooks,
          coursesByProgram: d.courses_by_program,
          topicsPerCourse: d.topics_per_course,
          coDistribution: d.co_distribution,
        };
      } catch {
        // fall through
      }
    }
    return mockAnalyticsData;
  },
};
