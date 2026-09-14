import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, BookOpen, Upload, BarChart2, Map, BookMarked, Settings, LayoutDashboard } from 'lucide-react';

const navItems = [
  { label: 'Assistant', path: '/', icon: <LayoutDashboard size={16} /> },
  { label: 'Courses', path: '/courses', icon: <BookOpen size={16} /> },
  { label: 'Syllabus Upload', path: '/syllabus', icon: <Upload size={16} /> },
  { label: 'CO/PO Mapping', path: '/mapping', icon: <Map size={16} /> },
  { label: 'Textbooks', path: '/textbooks', icon: <BookMarked size={16} /> },
  { label: 'Analytics', path: '/analytics', icon: <BarChart2 size={16} /> },
  { label: 'Settings', path: '/settings', icon: <Settings size={16} /> },
];

export default function NavMenu() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium text-sm transition-colors"
        aria-label="Open navigation menu"
        aria-expanded={open}
      >
        {open ? <X size={18} /> : <Menu size={18} />}
        <span className="hidden sm:inline">Menu</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden animate-message-in">
          {navItems.map(item => (
            <button
              key={item.path}
              onClick={() => { navigate(item.path); setOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left transition-colors
                ${location.pathname === item.path
                  ? 'bg-blue-50 text-blue-700 font-semibold'
                  : 'text-gray-700 hover:bg-gray-50'}`}
            >
              <span className="text-blue-500">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
