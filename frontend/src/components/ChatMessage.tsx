import { useState } from 'react';
import { Copy, Check, Bot, User } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../types';
import CitationCard from './CitationCard';
import { useToast } from '../context/ToastContext';

function formatTime(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderContent(text: string) {
  return text.split('\n').map((line, i) => {
    if (line.startsWith('• ')) {
      return (
        <div key={i} className="flex gap-2 my-0.5">
          <span className="text-blue-500 mt-0.5 shrink-0">•</span>
          <span>{line.slice(2)}</span>
        </div>
      );
    }
    if (line === '') return <div key={i} className="h-2" />;
    // Bold **text**
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return (
      <div key={i}>
        {parts.map((p, j) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={j}>{p.slice(2, -2)}</strong>
            : <span key={j}>{p}</span>
        )}
      </div>
    );
  });
}

interface Props {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: Props) {
  const [copied, setCopied] = useState(false);
  const { showToast } = useToast();
  const isAssistant = message.role === 'assistant';

  function handleCopy() {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true);
      showToast({ type: 'success', title: 'Copied to clipboard' });
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className={`animate-message-in w-full ${isAssistant ? '' : ''}`}>
      <div className={`rounded-xl border px-5 py-4 ${
        isAssistant
          ? 'bg-white border-blue-100 shadow-sm'
          : 'bg-blue-600 border-blue-600'
      }`}>
        {/* Header row */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className={`flex items-center justify-center w-6 h-6 rounded-full ${
              isAssistant ? 'bg-blue-100' : 'bg-white/20'
            }`}>
              {isAssistant
                ? <Bot size={13} className="text-blue-600" />
                : <User size={13} className="text-white" />
              }
            </div>
            <span className={`text-xs font-bold uppercase tracking-widest ${
              isAssistant ? 'text-blue-600' : 'text-white/90'
            }`}>
              {isAssistant ? 'Assistant' : 'You'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs ${isAssistant ? 'text-gray-400' : 'text-white/60'}`}>
              {formatTime(message.timestamp)}
            </span>
            {isAssistant && (
              <button
                onClick={handleCopy}
                title="Copy response"
                className="text-gray-300 hover:text-blue-500 transition-colors"
                aria-label="Copy response"
              >
                {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
              </button>
            )}
          </div>
        </div>

        {/* Message content */}
        <div className={`text-sm leading-relaxed ${isAssistant ? 'text-gray-700' : 'text-white'}`}>
          {renderContent(message.content)}
        </div>

        {/* Citations */}
        {isAssistant && message.citations && message.citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.citations.map(c => (
              <CitationCard key={c.id} citation={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Typing indicator
export function TypingIndicator() {
  return (
    <div className="animate-message-in w-full">
      <div className="rounded-xl border bg-white border-blue-100 shadow-sm px-5 py-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100">
            <Bot size={13} className="text-blue-600" />
          </div>
          <span className="text-xs font-bold uppercase tracking-widest text-blue-600">Assistant</span>
        </div>
        <div className="flex items-center gap-1.5 h-5">
          <div className="w-2 h-2 rounded-full bg-blue-400 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-blue-400 typing-dot" />
          <div className="w-2 h-2 rounded-full bg-blue-400 typing-dot" />
          <span className="text-xs text-gray-400 ml-1">Thinking...</span>
        </div>
      </div>
    </div>
  );
}
