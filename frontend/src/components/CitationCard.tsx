import { FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { syllabusService } from '../services/syllabusService';
import type { Citation } from '../types';

export default function CitationCard({ citation }: { citation: Citation }) {
  const navigate = useNavigate();
  const canOpenCourse = citation.courseId != null && (citation.unitNumber != null || Boolean(citation.unit));
  const canOpenDocument = citation.documentId != null && Boolean(citation.page) && !canOpenCourse;

  function handleClick() {
    if (canOpenCourse) {
      const params = new URLSearchParams();
      if (citation.unitNumber != null) params.set('unit', String(citation.unitNumber));
      if (citation.topicId) params.set('topic', citation.topicId);
      navigate(`/courses/${citation.courseId}${params.toString() ? `?${params}` : ''}`);
      return;
    }
    if (canOpenDocument && citation.documentId != null) {
      window.open(`${syllabusService.getDownloadUrl(citation.documentId)}${citation.page ? `#page=${citation.page}` : ''}`, '_blank', 'noopener,noreferrer');
    }
  }

  const label = citation.unit
    ? `Open ${citation.unit}${citation.topicName ? `, ${citation.topicName}` : ''} in ${citation.courseCode ?? citation.filename}`
    : `Open source ${citation.filename}`;
  const interactive = canOpenCourse || canOpenDocument;
  return (
    <button
      type="button"
      onClick={interactive ? handleClick : undefined}
      disabled={!interactive}
      aria-label={label}
      className={`inline-flex items-center gap-2 mt-2 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-700 text-left ${interactive ? 'cursor-pointer hover:bg-blue-100 hover:border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-400' : 'cursor-default'}`}
    >
      <FileText size={12} className="shrink-0 text-blue-500" />
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="font-semibold uppercase tracking-wide text-blue-400" style={{ fontSize: '10px' }}>SOURCE</span>
        <span className="font-medium">{citation.filename}</span>
        {citation.unit && (
          <>
            <span className="text-blue-300">·</span>
            <span>{citation.unit}</span>
            {citation.topicName && <><span className="text-blue-300">·</span><span>{citation.topicName}</span></>}
          </>
        )}
        {citation.page && (
          <>
            <span className="text-blue-300">·</span>
            <span>{citation.page}</span>
          </>
        )}
      </div>
    </button>
  );
}
