import { useState } from 'react';
import type { ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, BookOpen, Upload, MessageCircle, Map,
  BookMarked, BarChart2, Settings, HelpCircle, Menu, X,
  Bot, ChevronRight, GraduationCap, BookUser,
} from 'lucide-react';
import { useRole } from '../context/RoleContext';
import RoleSwitcher from './RoleSwitcher';

// ── Nav items — show/hide based on role ───────────────────────────────────────

const ALL_NAV_ITEMS = [
  { to: '/dashboard',  label: 'Dashboard',     icon: LayoutDashboard, facultyOnly: false },
  { to: '/courses',    label: 'Courses',        icon: BookOpen,        facultyOnly: false },
  { to: '/assistant',  label: 'AI Assistant',   icon: MessageCircle,   facultyOnly: false },
  { to: '/syllabus',   label: 'Syllabus',       icon: Upload,          facultyOnly: true  },
  { to: '/mapping',    label: 'CO / PO Mapping',icon: Map,             facultyOnly: false },
  { to: '/textbooks',  label: 'Textbooks',      icon: BookMarked,      facultyOnly: false },
  { to: '/analytics',  label: 'Analytics',      icon: BarChart2,       facultyOnly: false },
];

const BOTTOM_ITEMS = [
  { to: '/settings', label: 'Settings', icon: Settings },
];

// ── Sidebar link ──────────────────────────────────────────────────────────────

function SidebarLink({ to, label, icon: Icon, onClick }: {
  to: string; label: string; icon: React.ElementType; onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group
        ${isActive
          ? 'bg-blue-600 text-white shadow-sm shadow-blue-200'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon size={17} className={isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600'} />
          <span className="flex-1">{label}</span>
          {isActive && <ChevronRight size={13} className="text-blue-200" />}
        </>
      )}
    </NavLink>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function Sidebar({ onClose }: { onClose?: () => void }) {
  const { isFaculty, role } = useRole();

  const visibleNav = ALL_NAV_ITEMS.filter(item => isFaculty || !item.facultyOnly);

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-100">
      {/* Logo */}
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-sm">
            <Bot size={18} className="text-white" />
          </div>
          <div>
            <p className="font-black text-gray-900 text-sm leading-tight tracking-tight">CourseAI</p>
            <p className="text-xs text-gray-400 leading-tight">Course Content Agent</p>
          </div>
          {onClose && (
            <button onClick={onClose} className="ml-auto p-1 text-gray-400 hover:text-gray-600 lg:hidden" aria-label="Close menu">
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Role badge in sidebar */}
      <div className="px-3 py-2 border-b border-gray-50">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold
          ${role === 'faculty' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
          {role === 'faculty'
            ? <BookUser size={14} />
            : <GraduationCap size={14} />
          }
          <span>{role === 'faculty' ? 'Faculty' : 'Student'}</span>
          <span className="ml-auto text-xs font-normal opacity-60">
            {role === 'faculty' ? 'Full access' : 'Read-only'}
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
        {visibleNav.map(item => (
          <SidebarLink key={item.to} {...item} onClick={onClose} />
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-gray-100 space-y-2">
        {BOTTOM_ITEMS.map(item => (
          <SidebarLink key={item.to} {...item} onClick={onClose} />
        ))}
        <button className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all w-full">
          <HelpCircle size={17} className="text-slate-400" />
          <span>Help</span>
        </button>
        {/* Role switcher inside sidebar */}
        <div className="pt-1">
          <RoleSwitcher />
        </div>
      </div>
    </div>
  );
}

// ── AppShell ──────────────────────────────────────────────────────────────────

export default function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const currentNav = ALL_NAV_ITEMS.find(n => location.pathname.startsWith(n.to)) ??
    BOTTOM_ITEMS.find(n => location.pathname.startsWith(n.to));

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex w-56 shrink-0 h-full flex-col">
        <Sidebar />
      </div>

      {/* Mobile Sidebar Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
          <div className="relative w-64 h-full">
            <Sidebar onClose={() => setSidebarOpen(false)} />
          </div>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile top bar */}
        <header className="lg:hidden bg-white border-b border-gray-100 px-4 h-14 flex items-center gap-3 shrink-0 sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center">
              <Bot size={14} className="text-white" />
            </div>
            <span className="font-black text-gray-900 text-sm">CourseAI</span>
          </div>
          {currentNav && (
            <>
              <span className="text-gray-300">/</span>
              <span className="text-sm font-medium text-gray-600">{currentNav.label}</span>
            </>
          )}
          {/* Role switcher in mobile topbar */}
          <div className="ml-auto">
            <RoleSwitcher />
          </div>
        </header>

        {/* Scrollable page content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
