import { useState, useRef, useEffect } from 'react';
import { GraduationCap, BookUser, ChevronDown, Check } from 'lucide-react';
import { useRole, type Role } from '../context/RoleContext';
import { useToast } from '../context/ToastContext';

const ROLE_META: Record<Role, {
  label: string;
  desc: string;
  icon: React.ReactNode;
  badge: string;
  badgeBg: string;
}> = {
  faculty: {
    label: 'Faculty',
    desc: 'Upload & manage content',
    icon: <BookUser size={16} />,
    badge: 'text-blue-700',
    badgeBg: 'bg-blue-50 border-blue-200',
  },
  student: {
    label: 'Student',
    desc: 'Browse & learn',
    icon: <GraduationCap size={16} />,
    badge: 'text-green-700',
    badgeBg: 'bg-green-50 border-green-200',
  },
};

export default function RoleSwitcher() {
  const { role, setRole } = useRole();
  const { showToast } = useToast();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const meta = ROLE_META[role];

  useEffect(() => {
    function close(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  function switchTo(r: Role) {
    if (r === role) { setOpen(false); return; }
    setRole(r);
    setOpen(false);
    showToast({
      type: r === 'faculty' ? 'info' : 'success',
      title: `Switched to ${ROLE_META[r].label} mode`,
      message: ROLE_META[r].desc,
    });
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(v => !v)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm font-semibold transition-all hover:shadow-sm
          ${meta.badgeBg} ${meta.badge}`}
        aria-label="Switch role"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        {meta.icon}
        <span>{meta.label}</span>
        <ChevronDown size={13} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden animate-message-in"
          role="listbox"
          aria-label="Select role"
        >
          <div className="px-3 pt-2.5 pb-1 border-b border-gray-50">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Switch Role</p>
          </div>
          {(Object.entries(ROLE_META) as [Role, typeof ROLE_META[Role]][]).map(([r, m]) => (
            <button
              key={r}
              role="option"
              aria-selected={r === role}
              onClick={() => switchTo(r)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left transition-colors hover:bg-gray-50
                ${r === role ? 'bg-gray-50/80' : ''}`}
            >
              <span className={`${ROLE_META[r].badge}`}>{m.icon}</span>
              <div className="flex-1">
                <p className={`font-semibold ${ROLE_META[r].badge}`}>{m.label}</p>
                <p className="text-xs text-gray-400">{m.desc}</p>
              </div>
              {r === role && <Check size={14} className="text-blue-500 shrink-0" />}
            </button>
          ))}
          <div className="px-4 py-2 bg-gray-50/50 border-t border-gray-50">
            <p className="text-xs text-gray-400">
              Demo mode — role switching is for presentation only.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
