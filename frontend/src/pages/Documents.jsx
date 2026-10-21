import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  Trash2,
  Search,
  MessageSquareText,
  Award,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  FileUp,
} from 'lucide-react';
import documentService from '../services/documentService';
import { useToast } from '../context/ToastContext';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Badge from '../components/common/Badge';
import EmptyState from '../components/common/EmptyState';
import Modal from '../components/common/Modal';
import Spinner from '../components/common/Spinner';

export const Documents = () => {
  const navigate = useNavigate();
  const { success, error, warning, info } = useToast();
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await documentService.getDocuments();
      setDocuments(Array.isArray(data) ? data : data?.documents || []);
    } catch (err) {
      console.error('Failed to load documents:', err.message);
      setDocuments([]);
      if (!err.isOffline) {
        error(err.message || 'Failed to load documents.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // Poll for document status updates while any document is in Processing state
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => (d.status || '').toLowerCase() === 'processing'
    );
    if (!hasProcessing) return;

    const intervalId = setInterval(() => {
      loadDocuments();
    }, 3000);

    return () => clearInterval(intervalId);
  }, [documents]);

  const saveLocalDocs = (docs) => {
    setDocuments(docs);
    localStorage.setItem('ai_study_docs', JSON.stringify(docs));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processSelectedFile(e.target.files[0]);
    }
  };

  const processSelectedFile = async (file) => {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      error('Please select a valid PDF file. Other formats are not currently supported.');
      return;
    }

    // Validate size (max 25MB)
    const maxBytes = 25 * 1024 * 1024;
    if (file.size > maxBytes) {
      error(`File exceeds 25MB maximum limit (${(file.size / 1024 / 1024).toFixed(1)}MB).`);
      return;
    }

    setUploading(true);
    setUploadProgress(20);

    try {
      const response = await documentService.uploadDocument(file);
      setUploadProgress(100);
      success(`Successfully uploaded "${file.name}". Text extraction & chunking initiated.`);
      await loadDocuments();
    } catch (err) {
      error(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const confirmDelete = (doc) => {
    setDocumentToDelete(doc);
    setDeleteModalOpen(true);
  };

  const handleDelete = async () => {
    if (!documentToDelete) return;
    setDeleting(true);
    try {
      await documentService.deleteDocument(documentToDelete.id);
      success(`Document "${documentToDelete.filename}" deleted.`);
      await loadDocuments();
    } catch (err) {
      error(err.message || 'Failed to delete document.');
    } finally {
      setDeleting(false);
      setDeleteModalOpen(false);
      setDocumentToDelete(null);
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesQuery = (doc.filename || doc.name || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || (doc.status || 'Ready').toUpperCase() === statusFilter;
    return matchesQuery && matchesStatus;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Study Materials</h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload PDF notes, textbooks, and syllabi for text extraction, chunking, and semantic vector indexing.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          icon={RefreshCw}
          onClick={loadDocuments}
          loading={loading}
        >
          Refresh
        </Button>
      </div>

      {/* PDF Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center p-8 sm:p-10 rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer overflow-hidden group ${
          dragActive
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-slate-800 bg-slate-900/40 hover:border-indigo-500/50 hover:bg-slate-900/70'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleFileInputChange}
          disabled={uploading}
        />

        <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform shadow-lg">
          <FileUp className="w-8 h-8" />
        </div>

        <h3 className="text-base font-semibold text-slate-100">
          {uploading ? 'Processing document...' : 'Click to upload or drag & drop PDF'}
        </h3>
        <p className="text-xs text-slate-400 mt-1.5 max-w-sm text-center">
          Support for lecture slides, syllabi, and research papers up to 25MB.
        </p>

        {uploading && (
          <div className="w-full max-w-xs mt-4">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Extracting & Chunking...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Document Library Controls & List */}
      <div className="space-y-4">
        {/* Search & Status Filters */}
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search documents by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {['ALL', 'READY', 'PROCESSING', 'FAILED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors uppercase tracking-wider shrink-0 ${
                  statusFilter === st
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Documents Table / Card Display */}
        {loading ? (
          <div className="p-12 flex justify-center">
            <Spinner size="lg" label="Loading document index..." />
          </div>
        ) : filteredDocuments.length === 0 ? (
          <EmptyState
            icon={FileText}
            title={documents.length === 0 ? 'No Documents Uploaded Yet' : 'No Matching Documents'}
            description={
              documents.length === 0
                ? 'Upload course materials, slide decks, or textbook chapters to enable semantic pgvector retrieval.'
                : 'Try adjusting your search query or filter settings.'
            }
            actionText={documents.length === 0 ? 'Upload PDF Now' : undefined}
            actionIcon={Upload}
            onAction={() => fileInputRef.current?.click()}
          />
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {filteredDocuments.map((doc) => {
              const status = doc.status || 'Ready';
              return (
                <div
                  key={doc.id}
                  className="p-4 sm:p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:border-slate-700/80 transition-all shadow-md group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-11 h-11 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-slate-100 truncate group-hover:text-indigo-300 transition-colors">
                        {doc.filename || doc.name}
                      </h4>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-400">
                        {doc.file_size && (
                          <span>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                        )}
                        {doc.chunks_count !== undefined && (
                          <>
                            <span>•</span>
                            <span>{doc.chunks_count} vector chunks</span>
                          </>
                        )}
                        <span>•</span>
                        <span>
                          {doc.created_at
                            ? new Date(doc.created_at).toLocaleDateString()
                            : 'Indexed'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions & Status */}
                  <div className="flex items-center gap-3 self-end sm:self-auto shrink-0">
                    <Badge status={status} />

                    {status === 'Ready' && (
                      <>
                        <Button
                          size="sm"
                          variant="ghost"
                          icon={MessageSquareText}
                          onClick={() => navigate('/chat', { state: { documentId: doc.id } })}
                          title="Chat with this document"
                        >
                          Chat
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          icon={Award}
                          onClick={() => navigate('/quiz', { state: { documentId: doc.id } })}
                          title="Generate quiz from this document"
                        >
                          Quiz
                        </Button>
                      </>
                    )}

                    <button
                      onClick={() => confirmDelete(doc)}
                      className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Document"
        subtitle="Confirm deletion of indexed study material"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-300">
            Are you sure you want to delete{' '}
            <strong className="text-white">"{documentToDelete?.filename}"</strong>?
            This will remove all associated text chunks and vector embeddings.
          </p>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <Button
              variant="outline"
              size="md"
              onClick={() => setDeleteModalOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={handleDelete}
              loading={deleting}
              icon={Trash2}
            >
              Confirm Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Documents;
