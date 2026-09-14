import { useNavigate } from 'react-router-dom';
import { Bot } from 'lucide-react';
import NavMenu from './NavMenu';

export default function AppHeader() {
  const navigate = useNavigate();

  return (
    <header className="bg-white border-b border-gray-100 shadow-sm sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

        {/* Left — College logo */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-3 shrink-0 hover:opacity-80 transition-opacity"
          aria-label="Go to home"
        >
          {/* Emblem placeholder */}
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-700 to-indigo-800 flex items-center justify-center shadow-sm shrink-0">
            <span className="text-white font-black text-xs leading-none text-center">V</span>
          </div>
          <div className="hidden sm:block text-left">
            <p className="font-black text-blue-900 text-sm leading-none tracking-wide">VIGNAN'S</p>
            <p className="text-gray-500 text-xs leading-none mt-0.5">College of Engineering</p>
          </div>
        </button>

        {/* Center — Brand */}
        <div className="flex-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-gray-400 hidden sm:block">CSE Presents</p>
          <button
            onClick={() => navigate('/')}
            className="flex items-center justify-center gap-2 hover:opacity-80 transition-opacity"
          >
            <Bot size={18} className="text-blue-600 shrink-0" />
            <span className="font-black text-gray-900 text-base sm:text-lg tracking-tight uppercase">Course Content Agent</span>
          </button>
          <p className="text-xs text-blue-500 font-medium hidden sm:block">AI-powered University Syllabus Assistant</p>
        </div>

        {/* Right — Nav menu */}
        <div className="shrink-0">
          <NavMenu />
        </div>
      </div>
    </header>
  );
}
