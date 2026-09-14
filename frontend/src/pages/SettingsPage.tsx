import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { Settings, Bell, Palette, Database, Info } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { courseService } from '../services/courseService';

interface ToggleSetting {
  label: string;
  type: 'toggle';
  defaultChecked: boolean;
}
interface SelectSetting {
  label: string;
  type: 'select';
  defaultValue: string;
  options: string[];
}
type SettingItem = ToggleSetting | SelectSetting;

function ToggleRow({ label, defaultChecked }: ToggleSetting) {
  const [checked, setChecked] = useState(defaultChecked);
  const { showToast } = useToast();
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-700">{label}</span>
      <button
        onClick={() => { setChecked(v => !v); showToast({ type: 'success', title: 'Setting updated' }); }}
        className={`relative w-10 h-5 rounded-full transition-colors ${checked ? 'bg-blue-500' : 'bg-gray-200'}`}
        aria-label={`Toggle ${label}`}
        role="switch"
        aria-checked={checked}
      >
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? 'translate-x-5' : ''}`} />
      </button>
    </div>
  );
}

function SelectRow({ label, defaultValue, options }: SelectSetting) {
  const { showToast } = useToast();
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-700">{label}</span>
      <select
        defaultValue={defaultValue}
        onChange={() => showToast({ type: 'success', title: 'Setting saved' })}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

interface Section {
  icon: ReactNode;
  title: string;
  settings: SettingItem[];
}

const DEFAULT_REGULATION_KEY = 'courseai_default_regulation';

const sections: Section[] = [
  {
    icon: <Palette size={18} className="text-blue-500" />,
    title: 'Appearance',
    settings: [
      { label: 'Theme', type: 'select', defaultValue: 'Light', options: ['Light', 'System'] },
      { label: 'Language', type: 'select', defaultValue: 'English', options: ['English'] },
    ],
  },
  {
    icon: <Bell size={18} className="text-blue-500" />,
    title: 'Notifications',
    settings: [
      { label: 'Upload complete alerts', type: 'toggle', defaultChecked: true },
      { label: 'Processing notifications', type: 'toggle', defaultChecked: true },
    ],
  },
  {
    icon: <Database size={18} className="text-blue-500" />,
    title: 'Data & Storage',
    settings: [
      { label: 'Default Program', type: 'select', defaultValue: 'B.Tech CSE', options: ['B.Tech CSE', 'B.Tech ECE', 'B.Tech IT', 'MCA'] },
    ],
  },
];

function RegulationRow({ regulations, value, loading, onChange }: {
  regulations: string[];
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
}) {
  const { showToast } = useToast();
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-700">Default Regulation</span>
      <select
        value={value}
        disabled={loading || regulations.length === 0}
        onChange={event => {
          onChange(event.target.value);
          showToast({ type: 'success', title: 'Setting saved' });
        }}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50 disabled:text-gray-400"
        aria-label="Default Regulation"
      >
        {loading && <option value="">Loading...</option>}
        {!loading && regulations.length === 0 && <option value="">No regulations available</option>}
        {regulations.map(regulation => (
          <option key={regulation} value={regulation}>{regulation}</option>
        ))}
      </select>
    </div>
  );
}

export default function SettingsPage() {
  const [regulations, setRegulations] = useState<string[]>([]);
  const [defaultRegulation, setDefaultRegulation] = useState('');
  const [regulationsLoading, setRegulationsLoading] = useState(true);

  useEffect(() => {
    courseService.getRegulations()
      .then(available => {
        setRegulations(available);
        const saved = localStorage.getItem(DEFAULT_REGULATION_KEY);
        const selected = saved && available.includes(saved) ? saved : (available[0] ?? '');
        setDefaultRegulation(selected);
        if (selected) localStorage.setItem(DEFAULT_REGULATION_KEY, selected);
      })
      .catch(() => {
        setRegulations([]);
        setDefaultRegulation('');
      })
      .finally(() => setRegulationsLoading(false));
  }, []);

  function handleRegulationChange(value: string) {
    setDefaultRegulation(value);
    if (value) localStorage.setItem(DEFAULT_REGULATION_KEY, value);
    else localStorage.removeItem(DEFAULT_REGULATION_KEY);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings size={22} className="text-blue-500" /> Settings
        </h1>
        <p className="text-sm text-gray-500 mt-1">Configure your Course Content Agent preferences.</p>
      </div>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 space-y-5">
        {sections.map(section => (
          <div key={section.title} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              {section.icon}
              <h2 className="font-semibold text-gray-800">{section.title}</h2>
            </div>
            <div className="space-y-0">
              {section.title === 'Data & Storage' && (
                <RegulationRow
                  regulations={regulations}
                  value={defaultRegulation}
                  loading={regulationsLoading}
                  onChange={handleRegulationChange}
                />
              )}
              {section.settings.map(s => (
                s.type === 'toggle'
                  ? <ToggleRow key={s.label} {...s} />
                  : <SelectRow key={s.label} {...s} />
              ))}
            </div>
          </div>
        ))}

        {/* About */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <Info size={18} className="text-blue-500" />
            <h2 className="font-semibold text-gray-800">About</h2>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <p><span className="font-medium">App:</span> Course Content Agent</p>
            <p><span className="font-medium">Version:</span> 1.0.0</p>
            <p><span className="font-medium">Built for:</span> Vignan's College of Engineering Hackathon</p>
            <p className="text-xs text-gray-400 mt-2">AI-powered University Syllabus Assistant · CSE Department</p>
          </div>
        </div>
      </div>
    </div>
  );
}
