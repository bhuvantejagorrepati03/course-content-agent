// ============================================================
// Core TypeScript interfaces for Course Content Agent
// ============================================================

export interface Course {
  id: string;
  name: string;
  code: string;
  program: string;
  department: string;
  year: string;
  semester: string;
  regulation: string;
  credits: number;
  totalHours: number;
  description: string;
  prerequisites: string[];
  units: Unit[];
  courseOutcomes: CourseOutcome[];
  textbooks: Textbook[];
  referenceBooks: ReferenceBook[];
  mappings: COPOMapping[];
  status: 'indexed' | 'processing' | 'pending';
  uploadedAt: string;
  syllabusFile?: string;
  unitCount?: number;
  topicCount?: number;
  textbookCount?: number;
}

export interface Unit {
  id: string;
  number: number;
  title: string;
  hours: number;
  topics: Topic[];
  coMapping: string[];
  description?: string;
}

export interface Topic {
  id: string;
  title: string;
  subtopics?: string[];
  hours?: number;
  coMapping?: string[];
}

export interface CourseOutcome {
  id: string;
  code: string;
  description: string;
  bloomLevel?: string;
}

export interface Textbook {
  id: string;
  title: string;
  author: string;
  edition: string;
  publisher: string;
  year?: string;
  isbn?: string;
  courseIds: string[];
  unitRelevance?: number[];
  type: 'textbook';
}

export interface ReferenceBook {
  id: string;
  title: string;
  author: string;
  edition: string;
  publisher: string;
  year?: string;
  isbn?: string;
  courseIds: string[];
  type: 'reference';
}

export interface COPOMapping {
  courseOutcomeId: string;
  mappings: { [key: string]: number };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  isTyping?: boolean;
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
  section?: string;
}

export interface SyllabusDocument {
  id: string;
  filename: string;
  fileSize: number;
  uploadedAt: string;
  courseId?: string;
  status: 'uploading' | 'processing' | 'indexed' | 'failed';
  progress?: number;
  extractedData?: {
    units: number;
    topics: number;
    courseOutcomes: number;
    textbooks: number;
  };
}

export interface AnalyticsData {
  totalCourses: number;
  totalDocuments: number;
  totalTopics: number;
  totalCOs: number;
  coursesByProgram: { program: string; count: number }[];
  topicsPerCourse: { course: string; topics: number }[];
  coDistribution: { level: string; count: number }[];
  unitsProcessed: number;
  textbooksExtracted: number;
}

export interface FilterOptions {
  program?: string;
  year?: string;
  regulation?: string;
  department?: string;
  status?: string;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
  duration?: number;
}
