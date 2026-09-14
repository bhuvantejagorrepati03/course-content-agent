import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { RoleProvider } from './context/RoleContext';
import ToastContainer from './components/Toast';
import AppShell from './components/AppShell';
import DashboardPage from './pages/DashboardPage';
import AssistantPage from './pages/AssistantPage';
import CoursesPage from './pages/CoursesPage';
import CourseDetailPage from './pages/CourseDetailPage';
import SyllabusPage from './pages/SyllabusPage';
import MappingPage from './pages/MappingPage';
import TextbooksPage from './pages/TextbooksPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <RoleProvider>
          <AppShell>
            <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/courses" element={<CoursesPage />} />
            <Route path="/courses/:id" element={<CourseDetailPage />} />
            <Route path="/syllabus" element={<SyllabusPage />} />
            <Route path="/mapping" element={<MappingPage />} />
            <Route path="/textbooks" element={<TextbooksPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          </AppShell>
          <ToastContainer />
        </RoleProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
