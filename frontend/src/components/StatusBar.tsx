import { Mic, FileText } from 'lucide-react';

export default function StatusBar() {
  return (
    <div className="bg-white border-t border-gray-100 px-4 sm:px-6 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
          </span>
          <span className="text-xs text-gray-500 font-medium">AI Assistant Online</span>
          <span className="hidden sm:inline text-gray-300">|</span>
          <span className="hidden sm:inline text-xs text-gray-400">Ready</span>
        </div>

        {/* Center */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-gray-400">
          <span className="font-medium text-gray-500">Course Content Agent</span>
          <span>·</span>
          <span>AI-powered syllabus assistance</span>
        </div>

        {/* Right — Quick actions */}
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-blue-600 transition-colors" aria-label="Voice input (coming soon)" title="Voice input (coming soon)">
            <Mic size={13} />
            <span className="hidden sm:inline">Voice</span>
          </button>
          <button className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-blue-600 transition-colors" aria-label="Transcript" title="Transcript">
            <FileText size={13} />
            <span className="hidden sm:inline">Transcript</span>
          </button>
        </div>
      </div>
    </div>
  );
}
