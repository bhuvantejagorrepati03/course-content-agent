import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Trash2, ChevronDown, BookOpen, ExternalLink } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../types';
import { aiService, type AIChatMessage, type Resource } from '../services/aiService';
import { API_BASE } from '../services/api';
import AIRobotHero from '../components/AIRobotHero';
import ChatMessageComponent, { TypingIndicator } from '../components/ChatMessage';
import { useToast } from '../context/ToastContext';

// ── Types ──────────────────────────────────────────────────────────────────────

interface ExtendedMessage extends ChatMessageType {
  resources?: Resource[];
}

interface HistoryEntry {
  role: 'user' | 'assistant';
  content: string;
}

interface CourseOption {
  id: number;
  name: string;
  code: string;
  regulation: string;
}

function genId() { return Math.random().toString(36).substring(2, 9); }

// ── Welcome messages ───────────────────────────────────────────────────────────

function makeWelcome(): ExtendedMessage[] {
  return [
    {
      id: 'w1',
      role: 'assistant',
      content:
        "Hi! I'm your Course Content Assistant. I can answer any question about the selected course — units, topics, textbooks, course outcomes, comparisons, study advice, or anything else.",
      timestamp: new Date(Date.now() - 120000),
    },
    {
      id: 'w2',
      role: 'assistant',
      content: 'Select a regulation and course below, then ask me anything.',
      timestamp: new Date(Date.now() - 60000),
    },
  ];
}

// ── Resource card ──────────────────────────────────────────────────────────────

function ResourceCard({ resource }: { resource: Resource }) {
  return (
    <div className="mt-2 flex items-center gap-3 px-3 py-2.5 bg-blue-50 border border-blue-100 rounded-lg text-sm">
      <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
        <BookOpen size={14} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-800 truncate">{resource.title}</p>
        {resource.author && <p className="text-xs text-gray-500">by {resource.author}</p>}
        <p className="text-xs text-blue-500 capitalize">{resource.resource_type}</p>
      </div>
      {resource.url ? (
        <a
          href={resource.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 flex items-center gap-1 text-xs font-semibold text-blue-700 bg-white border border-blue-200 rounded-lg px-2.5 py-1.5 hover:bg-blue-100 transition-colors"
          aria-label={`Open ${resource.title}`}
        >
          <ExternalLink size={12} /> Open
        </a>
      ) : (
        <span className="shrink-0 text-xs text-gray-400 italic">No digital copy</span>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function AssistantPage() {
  // Regulation / course selectors — driven by backend data
  const [regulations, setRegulations] = useState<string[]>([]);
  const [selectedRegulation, setSelectedRegulation] = useState('');
  const [courses, setCourses] = useState<CourseOption[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState('');

  // Chat state
  const [messages, setMessages] = useState<ExtendedMessage[]>(makeWelcome());
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMsg, setStreamingMsg] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { showToast } = useToast();

  // ── Fetch regulations on mount ────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API_BASE}/api/regulations`)
      .then(r => r.json())
      .then(json => {
        if (json.success && Array.isArray(json.data)) {
          const regs = json.data.map((r: { code: string }) => r.code).filter(Boolean);
          setRegulations(regs);
          if (regs.length > 0) setSelectedRegulation(regs[0]);
        }
      })
      .catch(err => console.warn('[AssistantPage] Failed to fetch regulations:', err));
  }, []);

  // ── Fetch courses when regulation changes ─────────────────────────────────
  useEffect(() => {
    if (!selectedRegulation) return;
    fetch(`${API_BASE}/api/courses?regulation=${encodeURIComponent(selectedRegulation)}`)
      .then(r => r.json())
      .then(json => {
        if (json.success && Array.isArray(json.data)) {
          const opts: CourseOption[] = json.data.map((c: {
            id: number; course_name: string; course_code: string; regulation: string;
          }) => ({
            id: c.id,
            name: c.course_name,
            code: c.course_code,
            regulation: c.regulation,
          }));
          setCourses(opts);
          if (opts.length > 0) setSelectedCourseId(String(opts[0].id));
        }
      })
      .catch(err => console.warn('[AssistantPage] Failed to fetch courses:', err));
  }, [selectedRegulation]);

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, streamingMsg]);

  // ── Send message ──────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isTyping) return;
    setInput('');

    const userMsg: ExtendedMessage = {
      id: genId(), role: 'user', content: text.trim(), timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);
    setStreamingMsg('');

    const currentHistory = history;

    try {
      const response = await aiService.sendMessage(
        text.trim(),
        selectedCourseId,
        selectedRegulation,
        currentHistory,
        (partial) => { setIsTyping(false); setStreamingMsg(partial); },
      ) as AIChatMessage;

      setIsTyping(false);
      setStreamingMsg('');

      const assistantMsg: ExtendedMessage = {
        id: response.id, role: 'assistant', content: response.content,
        timestamp: response.timestamp, citations: response.citations,
        resources: response.resources,
      };
      setMessages(prev => [...prev, assistantMsg]);
      setHistory(prev => [
        ...prev,
        { role: 'user', content: text.trim() },
        { role: 'assistant', content: response.content },
      ]);
    } catch {
      setIsTyping(false);
      setStreamingMsg('');
      setMessages(prev => [...prev, {
        id: genId(), role: 'assistant',
        content: 'Something went wrong. Please try again.',
        timestamp: new Date(),
      }]);
    }
  }, [isTyping, selectedCourseId, selectedRegulation, history]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
  }

  function handleClear() {
    setMessages(makeWelcome());
    setHistory([]);
    showToast({ type: 'info', title: 'Chat cleared' });
  }

  function handleRegulationChange(reg: string) {
    setSelectedRegulation(reg);
    setMessages(makeWelcome());
    setHistory([]);
  }

  function handleCourseChange(id: string) {
    setSelectedCourseId(id);
    const c = courses.find(o => String(o.id) === id);
    setMessages([
      ...makeWelcome(),
      {
        id: genId(), role: 'assistant',
        content: c
          ? `Switched to **${c.name}** (${c.code} · ${c.regulation}). Ask me anything!`
          : 'Course changed. Ask me anything!',
        timestamp: new Date(),
      },
    ]);
    setHistory([]);
  }

  const suggestedQuestions = aiService.getSuggestedQuestions(selectedCourseId);
  const isFirstExchange = messages.length <= 3;
  const selectedCourse = courses.find(c => String(c.id) === selectedCourseId);

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-br from-blue-50 via-sky-50 to-indigo-50 border-b border-blue-100">
        <AIRobotHero />

        {/* Selectors */}
        <div className="flex flex-wrap justify-center gap-3 pb-5 px-4">
          {/* Regulation */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-blue-500 px-1">
              Regulation
            </label>
            <div className="relative">
              <select
                value={selectedRegulation}
                onChange={e => handleRegulationChange(e.target.value)}
                className="appearance-none bg-white border border-blue-200 rounded-lg pl-3 pr-8 py-2 text-sm font-medium text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer min-w-[90px]"
                aria-label="Select regulation"
              >
                {regulations.length === 0 && <option value="">Loading...</option>}
                {regulations.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Course */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold uppercase tracking-wider text-blue-500 px-1">
              Course
            </label>
            <div className="relative">
              <select
                value={selectedCourseId}
                onChange={e => handleCourseChange(e.target.value)}
                className="appearance-none bg-white border border-blue-200 rounded-lg pl-3 pr-8 py-2 text-sm font-medium text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer min-w-[200px]"
                aria-label="Select course"
                disabled={courses.length === 0}
              >
                {courses.length === 0 && <option value="">No courses yet — upload a syllabus</option>}
                {courses.map(c => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name} — {c.code}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* ── Chat area ───────────────────────────────────────────────────── */}
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 py-5 flex flex-col gap-3">
        {/* Status badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-full border border-blue-100">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-xs font-medium text-blue-700">
              {selectedCourse
                ? `${selectedCourse.code} · ${selectedCourse.regulation}`
                : selectedRegulation || 'No course selected'}
              {history.length > 0 && (
                <span className="ml-1.5 text-blue-400">
                  · {Math.floor(history.length / 2)} turn{Math.floor(history.length / 2) !== 1 ? 's' : ''}
                </span>
              )}
            </span>
          </div>
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-500 transition-colors px-2 py-1 rounded"
            aria-label="Clear chat"
          >
            <Trash2 size={13} /> Clear
          </button>
        </div>

        {/* Messages */}
        {messages.map(msg => (
          <div key={msg.id} className="flex flex-col gap-1">
            <ChatMessageComponent message={msg} />
            {msg.role === 'assistant' && msg.resources && msg.resources.length > 0 && (
              <div className="flex flex-col gap-1.5 pl-0">
                {msg.resources.map((r, i) => <ResourceCard key={i} resource={r} />)}
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && !streamingMsg && <TypingIndicator />}
        {streamingMsg && (
          <div className="animate-message-in w-full">
            <div className="rounded-xl border bg-white border-blue-100 shadow-sm px-5 py-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100">
                  <span className="text-blue-600 text-xs font-bold">AI</span>
                </div>
                <span className="text-xs font-bold uppercase tracking-widest text-blue-600">Assistant</span>
              </div>
              <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {streamingMsg}
                <span className="inline-block w-0.5 h-4 bg-blue-500 ml-0.5 animate-pulse align-middle" />
              </div>
            </div>
          </div>
        )}

        {/* Suggested questions */}
        {isFirstExchange && !isTyping && !streamingMsg && (
          <div className="pt-1">
            <p className="text-xs text-gray-400 mb-2 px-1">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map(q => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="px-3.5 py-2 text-xs font-medium bg-white border border-blue-200 text-blue-700 rounded-full hover:bg-blue-50 hover:border-blue-400 transition-all shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ───────────────────────────────────────────────────── */}
      <div className="sticky bottom-0 bg-white border-t border-gray-100 shadow-[0_-4px_20px_rgba(0,0,0,0.06)]">
        <div className="max-w-3xl mx-auto px-4 py-3">
          <div className="flex items-end gap-3 bg-gray-50 border border-blue-200 rounded-2xl px-4 py-3 focus-within:border-blue-400 focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about the course — units, topics, textbooks, outcomes..."
              rows={1}
              className="flex-1 bg-transparent text-sm text-gray-700 placeholder-gray-400 resize-none outline-none leading-relaxed max-h-32 overflow-y-auto"
              style={{ minHeight: '24px' }}
              aria-label="Chat input"
              disabled={isTyping}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isTyping}
              className="shrink-0 w-9 h-9 rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:cursor-not-allowed flex items-center justify-center transition-all shadow-sm hover:shadow-md active:scale-95"
              aria-label="Send message"
            >
              <Send size={15} className={input.trim() && !isTyping ? 'text-white' : 'text-gray-400'} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Enter</kbd> to send ·{' '}
            <kbd className="px-1 py-0.5 bg-gray-100 rounded text-xs">Shift+Enter</kbd> for new line
          </p>
        </div>
      </div>
    </div>
  );
}
