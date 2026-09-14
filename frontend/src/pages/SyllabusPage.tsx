import { useState, useRef, useCallback, useEffect } from 'react';
import {
  Upload, FileText, X, CheckCircle, Loader2, AlertCircle,
  Trash2, Download, Eye, RefreshCw, FileUp,
} from 'lucide-react';
import { syllabusService, type BackendDocument } from '../services/syllabusService';
import { useToast } from '../context/ToastContext';

// ── Types ──────────────────────────────────────────────────────────────────────

type Stage = 'idle' | 'selected' | 'processing' | 'done' | 'error';

const PROCESSING_STEPS = [
  'Uploading file...',
  'Analyzing syllabus structure...',
  'Extracting unit information...',
  'Identifying topics...',
  'Mapping course outcomes...',
  'Indexing content...',
  'Finalizing...',
];

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatBytes(bytes: number) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

const STATUS_BADGE: Record<string, string> = {
  uploaded:   'bg-blue-50 text-blue-600',
  processing: 'bg-amber-50 text-amber-600',
  completed:  'bg-green-50 text-green-700',
  failed:     'bg-red-50 text-red-600',
};

const FILE_TYPE_COLOR: Record<string, string> = {
  pdf:  'bg-red-50 text-red-600',
  docx: 'bg-blue-50 text-blue-600',
  pptx: 'bg-orange-50 text-orange-600',
};

// ── Document row ───────────────────────────────────────────────────────────────

function DocumentRow({
  doc,
  onDelete,
  onRefresh,
}: {
  doc: BackendDocument;
  onDelete: (id: number) => void;
  onRefresh: (id: number) => void;
}) {
  const [deleting, setDeleting] = useState(false);
  const { showToast } = useToast();

  async function handleDelete() {
    if (!confirm(`Delete "${doc.original_filename}"? This will also remove its indexed content from the AI.`)) return;
    setDeleting(true);
    try {
      await syllabusService.deleteDocument(doc.document_id);
      showToast({ type: 'success', title: 'Document deleted', message: 'Indexed content has been removed.' });
      onDelete(doc.document_id);
    } catch (err) {
      showToast({ type: 'error', title: 'Delete failed', message: String(err) });
      setDeleting(false);
    }
  }

  const downloadUrl = syllabusService.getDownloadUrl(doc.document_id);
  const hasExtractions = doc.extracted_units > 0 || doc.extracted_topics > 0;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        {/* File type badge */}
        <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-bold text-xs uppercase ${FILE_TYPE_COLOR[doc.file_type] ?? 'bg-gray-50 text-gray-500'}`}>
          {doc.file_type}
        </div>

        {/* Main info */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <p className="font-semibold text-gray-900 text-sm truncate max-w-[280px]" title={doc.original_filename}>
              {doc.original_filename}
            </p>
            <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize ${STATUS_BADGE[doc.status] ?? 'bg-gray-50 text-gray-500'}`}>
              {doc.status}
            </span>
          </div>

          <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-gray-500">
            <span>{formatBytes(doc.file_size)}</span>
            <span>{formatDate(doc.uploaded_at)}</span>
            {doc.course_name && (
              <span className="text-blue-600 font-medium">{doc.course_name}</span>
            )}
          </div>

          {/* Extraction stats */}
          {hasExtractions && (
            <div className="flex flex-wrap gap-2 mt-2">
              {doc.extracted_units > 0 && (
                <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">{doc.extracted_units} Units</span>
              )}
              {doc.extracted_topics > 0 && (
                <span className="text-xs px-2 py-0.5 bg-purple-50 text-purple-600 rounded-full">{doc.extracted_topics} Topics</span>
              )}
              {doc.extracted_outcomes > 0 && (
                <span className="text-xs px-2 py-0.5 bg-green-50 text-green-600 rounded-full">{doc.extracted_outcomes} COs</span>
              )}
              {doc.extracted_textbooks > 0 && (
                <span className="text-xs px-2 py-0.5 bg-amber-50 text-amber-600 rounded-full">{doc.extracted_textbooks} Books</span>
              )}
            </div>
          )}

          {doc.error_message && (
            <p className="text-xs text-red-500 mt-1 truncate" title={doc.error_message}>
              ⚠ {doc.error_message}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="shrink-0 flex items-center gap-1">
          {/* Refresh status for in-progress docs */}
          {(doc.status === 'processing' || doc.status === 'uploaded') && (
            <button
              onClick={() => onRefresh(doc.document_id)}
              title="Refresh status"
              className="p-2 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
              aria-label="Refresh"
            >
              <RefreshCw size={15} />
            </button>
          )}

          {/* View/Open inline */}
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="View / open"
            className="p-2 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            aria-label="Open"
          >
            <Eye size={15} />
          </a>

          {/* Download */}
          <a
            href={downloadUrl}
            download={doc.original_filename}
            title="Download"
            className="p-2 rounded-lg text-gray-400 hover:text-green-600 hover:bg-green-50 transition-colors"
            aria-label="Download"
          >
            <Download size={15} />
          </a>

          {/* Delete */}
          <button
            onClick={handleDelete}
            disabled={deleting}
            title="Delete document and remove indexed content"
            className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-40"
            aria-label="Delete"
          >
            {deleting ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function SyllabusPage() {
  // Upload state
  const [stage, setStage] = useState<Stage>('idle');
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState<{
    units: number; topics: number; courseOutcomes: number; textbooks: number; documentId: number;
  } | null>(null);
  const [duplicateMsg, setDuplicateMsg] = useState('');
  const [formData, setFormData] = useState({
    courseName: '', courseCode: '', program: 'B.Tech CSE',
    department: 'Computer Science & Engineering', year: 'II Year',
    semester: '3rd Semester', regulation: 'R23', credits: '4',
  });

  // Document list state
  const [docs, setDocs] = useState<BackendDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  const fileRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  // Load document list on mount
  useEffect(() => {
    loadDocs();
  }, []);

  async function loadDocs() {
    setDocsLoading(true);
    const data = await syllabusService.listDocuments();
    setDocs(data);
    setDocsLoading(false);
  }

  async function refreshDocStatus(docId: number) {
    try {
      const updated = await syllabusService.getDocumentStatus(docId);
      setDocs(prev => prev.map(d => d.document_id === docId ? updated : d));
    } catch {
      showToast({ type: 'error', title: 'Could not refresh status' });
    }
  }

  // ── File validation ────────────────────────────────────────────────────────

  const acceptFile = useCallback((f: File) => {
    const ext = f.name.split('.').pop()?.toLowerCase() ?? '';
    if (!['pdf', 'docx', 'pptx', 'ppt'].includes(ext)) {
      showToast({ type: 'error', title: 'Unsupported file', message: 'Accepted: PDF, DOCX, PPTX' });
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      showToast({ type: 'error', title: 'File too large', message: 'Maximum file size is 20 MB.' });
      return;
    }
    setFile(f);
    setDuplicateMsg('');
    setStage('selected');
    setFormData(prev => ({ ...prev, courseName: f.name.replace(/\.(pdf|docx|pptx|ppt)$/i, '') }));
  }, [showToast]);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) acceptFile(f);
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) acceptFile(f);
    // Reset input so same file can be re-selected
    if (fileRef.current) fileRef.current.value = '';
  }

  // ── Upload & process ────────────────────────────────────────────────────────

  async function handleProcess() {
    if (!file) return;
    setStage('processing');
    setProgress(0);
    setCurrentStep(PROCESSING_STEPS[0]);
    setDuplicateMsg('');

    try {
      const res = await syllabusService.processFile(
        file,
        (step, pct) => { setCurrentStep(step); setProgress(pct); },
      );
      setResult(res);
      setStage('done');
      showToast({ type: 'success', title: 'Syllabus processed!', message: 'Content has been indexed.' });
      // Reload document list so new doc appears immediately
      await loadDocs();
    } catch (err) {
      const msg = String(err);
      if (msg.startsWith('DUPLICATE:')) {
        setDuplicateMsg(msg.replace('DUPLICATE:', ''));
        setStage('selected');
        showToast({ type: 'warning', title: 'Duplicate file', message: msg.replace('DUPLICATE:', '') });
      } else {
        setStage('error');
        showToast({ type: 'error', title: 'Processing failed', message: msg });
      }
    }
  }

  // ── Delete handler ─────────────────────────────────────────────────────────

  function handleDeleteDoc(deletedId: number) {
    setDocs(prev => prev.filter(d => d.document_id !== deletedId));
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-100 px-6 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Syllabus Documents</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload syllabus PDFs and other course documents. The AI will extract and index all content automatically.
        </p>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8">

        {/* ── Upload Section ─────────────────────────────────────────────── */}
        <section>
          <h2 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
            <FileUp size={18} className="text-blue-500" /> Upload New Document
          </h2>

          <div className="space-y-4">
            {/* Drop zone */}
            {stage === 'idle' && (
              <div
                onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all
                  ${isDragging ? 'border-blue-500 bg-blue-50 scale-[1.01]' : 'border-blue-200 bg-white hover:border-blue-400 hover:bg-blue-50/50'}`}
              >
                <Upload size={40} className={`mx-auto mb-3 ${isDragging ? 'text-blue-600' : 'text-blue-400'}`} />
                <p className="text-base font-semibold text-gray-800 mb-1">Drag & drop your document here</p>
                <p className="text-sm text-gray-500 mb-3">or click to browse</p>
                <div className="flex justify-center gap-2 text-xs text-gray-400">
                  {['PDF', 'DOCX', 'PPTX'].map(t => (
                    <span key={t} className="px-2 py-1 bg-gray-100 rounded-full">{t}</span>
                  ))}
                  <span className="px-2 py-1 bg-gray-100 rounded-full">Max 20 MB</span>
                </div>
                <input ref={fileRef} type="file" accept=".pdf,.docx,.pptx,.ppt" className="hidden" onChange={handleFileInput} />
              </div>
            )}

            {/* File selected / processing */}
            {(stage === 'selected' || stage === 'processing') && file && (
              <>
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center shrink-0">
                    <FileText size={20} className="text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">{formatBytes(file.size)}</p>
                  </div>
                  {stage === 'selected' && (
                    <button
                      onClick={() => { setFile(null); setStage('idle'); setDuplicateMsg(''); }}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Remove file"
                    >
                      <X size={18} />
                    </button>
                  )}
                </div>

                {/* Duplicate warning */}
                {duplicateMsg && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
                    <AlertCircle size={16} className="shrink-0" />
                    {duplicateMsg}
                  </div>
                )}

                {/* Metadata form */}
                {stage === 'selected' && (
                  <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                    <h3 className="font-semibold text-gray-800 mb-4">Course Information (optional)</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {([
                        { key: 'courseName', label: 'Course Name' },
                        { key: 'courseCode', label: 'Course Code' },
                        { key: 'program', label: 'Program' },
                        { key: 'department', label: 'Department' },
                        { key: 'year', label: 'Year' },
                        { key: 'semester', label: 'Semester' },
                        { key: 'regulation', label: 'Regulation' },
                        { key: 'credits', label: 'Credits' },
                      ] as const).map(field => (
                        <div key={field.key}>
                          <label className="block text-xs font-semibold text-gray-500 mb-1">{field.label}</label>
                          <input
                            type="text"
                            value={formData[field.key]}
                            onChange={e => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-gray-50"
                          />
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={handleProcess}
                      className="mt-5 px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors shadow-sm"
                    >
                      Process Syllabus
                    </button>
                  </div>
                )}

                {/* Processing progress */}
                {stage === 'processing' && (
                  <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <Loader2 size={22} className="text-blue-600 animate-spin" />
                      <p className="font-semibold text-gray-800">{currentStep}</p>
                    </div>
                    <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden mb-4">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="space-y-1.5">
                      {PROCESSING_STEPS.map((step, i) => {
                        const currentIdx = PROCESSING_STEPS.indexOf(currentStep);
                        const completed = currentIdx > i;
                        const active = currentIdx === i;
                        return (
                          <div key={step} className={`flex items-center gap-2 text-sm transition-colors
                            ${active ? 'text-blue-700 font-medium' : completed ? 'text-green-600' : 'text-gray-400'}`}>
                            {completed
                              ? <CheckCircle size={14} />
                              : active
                                ? <Loader2 size={14} className="animate-spin" />
                                : <div className="w-3.5 h-3.5 rounded-full border border-gray-300" />
                            }
                            {step}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Success state */}
            {stage === 'done' && result && (
              <div className="bg-white rounded-xl border border-green-100 shadow-sm p-7 text-center">
                <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle size={26} className="text-green-500" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Syllabus Processed Successfully!</h3>
                <p className="text-sm text-gray-500 mb-5">All content has been indexed and is ready to query.</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {[
                    { label: 'Units', value: result.units },
                    { label: 'Topics', value: result.topics },
                    { label: 'Course Outcomes', value: result.courseOutcomes },
                    { label: 'Textbooks', value: result.textbooks },
                  ].map(s => (
                    <div key={s.label} className="bg-blue-50 rounded-xl p-3">
                      <p className="text-2xl font-bold text-blue-700">{s.value}</p>
                      <p className="text-xs text-blue-500 mt-0.5">{s.label}</p>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => { setStage('idle'); setFile(null); setResult(null); }}
                  className="px-6 py-2.5 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 text-sm font-medium transition-colors"
                >
                  Upload Another
                </button>
              </div>
            )}

            {/* Error state */}
            {stage === 'error' && (
              <div className="bg-white rounded-xl border border-red-100 shadow-sm p-6 text-center">
                <AlertCircle size={32} className="mx-auto text-red-400 mb-2" />
                <p className="font-semibold text-gray-800 mb-1">Processing Failed</p>
                <p className="text-sm text-gray-500 mb-4">Something went wrong. Check the backend logs.</p>
                <button
                  onClick={() => setStage('selected')}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </section>

        {/* ── Uploaded Documents Section ─────────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
              <FileText size={18} className="text-blue-500" />
              Uploaded Documents
              {docs.length > 0 && (
                <span className="ml-1 text-xs font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                  {docs.length}
                </span>
              )}
            </h2>
            <button
              onClick={loadDocs}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-blue-600 transition-colors px-2 py-1 rounded"
              aria-label="Refresh document list"
            >
              <RefreshCw size={13} /> Refresh
            </button>
          </div>

          {docsLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-100 p-4 animate-pulse">
                  <div className="flex gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3.5 bg-gray-100 rounded w-2/3" />
                      <div className="h-3 bg-gray-50 rounded w-1/3" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : docs.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
              <FileText size={36} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500 font-medium">No documents uploaded yet</p>
              <p className="text-sm text-gray-400 mt-1">Upload a syllabus PDF above to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map(doc => (
                <DocumentRow
                  key={doc.document_id}
                  doc={doc}
                  onDelete={handleDeleteDoc}
                  onRefresh={refreshDocStatus}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
