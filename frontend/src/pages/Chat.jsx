import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Send,
  MessageSquareText,
  ShieldCheck,
  FileText,
  Sparkles,
  Trash2,
  Bookmark,
  ChevronDown,
  ChevronUp,
  GraduationCap,
  Info,
  Copy,
  Check,
} from 'lucide-react';
import chatService from '../services/chatService';
import documentService from '../services/documentService';
import { useToast } from '../context/ToastContext';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';

export const Chat = () => {
  const location = useLocation();
  const { success, error, info } = useToast();
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const initialDocumentId = location.state?.documentId || '';
  const [selectedDocId, setSelectedDocId] = useState(initialDocumentId);
  const [documents, setDocuments] = useState([]);

  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [sending, setSending] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [copiedIndex, setCopiedIndex] = useState(null);

  // Load available documents and chat history
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await documentService.getDocuments();
        const docList = Array.isArray(data) ? data : data?.documents || [];
        setDocuments(docList);
      } catch (err) {
        console.error('Failed to load documents for chat:', err.message);
      }

      try {
        const historyData = await chatService.getChatHistory();
        if (Array.isArray(historyData) && historyData.length > 0) {
          setMessages(historyData);
        }
      } catch (err) {
        console.error('Failed to load chat history:', err.message);
      }
    };
    fetchData();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const handleSend = async (e) => {
    e?.preventDefault();
    const query = inputQuery.trim();
    if (!query || sending) return;

    const userMessage = {
      id: 'msg_' + Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setSending(true);

    try {
      const response = await chatService.sendMessage({
        query,
        documentId: selectedDocId || null,
      });

      const assistantMessage = {
        id: 'msg_ai_' + Date.now(),
        sender: 'assistant',
        text: response.answer || response.response || 'No response returned.',
        sources: response.sources || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      error(err.message || 'Failed to get answer from study assistant.');
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleSource = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const copyMessage = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const clearChat = async () => {
    try {
      await chatService.clearChat();
      setMessages([]);
      info('Conversation cleared.');
    } catch (err) {
      error(err.message || 'Failed to clear chat.');
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] min-h-[550px] animate-in fade-in duration-300">
      {/* Top Bar: Scope Selector & Grounded Notice */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 mb-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Study Context:
          </label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-slate-950 border border-slate-700/80 text-xs text-slate-100 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Uploaded Materials</option>
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename || d.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          {/* Grounded Banner */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Responses are grounded in retrieved study material</span>
            <span className="sm:hidden">Grounded RAG</span>
          </div>

          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              title="Clear conversation"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-5 rounded-2xl border border-slate-800/60 bg-slate-900/40 p-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 sm:p-12">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
              <MessageSquareText className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-slate-100">
              Grounded AI Academic Tutor
            </h3>
            <p className="text-xs text-slate-400 max-w-md mt-2 mb-6 leading-relaxed">
              Ask questions directly against your indexed PDFs. Answers cite specific chunks and text passages.
            </p>

            {/* Quick Prompt Starters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-lg w-full">
              {[
                'What are the core concepts covered in Chapter 1?',
                'Explain the difference between supervised and unsupervised learning.',
                'Generate a high-yield summary of key definitions.',
                'What potential exam questions could be derived from this text?',
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => setInputQuery(prompt)}
                  className="p-3 text-left rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs text-slate-300 hover:text-white hover:bg-slate-800 hover:border-indigo-500/40 transition-all flex items-start gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id || idx}
                className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
                    isUser
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-md'
                  }`}
                >
                  {isUser ? 'You' : <Sparkles className="w-4 h-4" />}
                </div>

                {/* Content Bubble */}
                <div className={`space-y-2 min-w-0 ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'bg-indigo-600 text-white rounded-tr-none'
                        : 'bg-slate-800/90 text-slate-100 border border-slate-700/70 rounded-tl-none'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.text}</div>

                    {!isUser && (
                      <div className="mt-3 pt-2.5 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-400">
                        <span className="text-[11px]">{msg.timestamp}</span>
                        <button
                          onClick={() => copyMessage(msg.text, idx)}
                          className="flex items-center gap-1 hover:text-slate-200 transition-colors"
                        >
                          {copiedIndex === idx ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Sources Preview (RAG Grounding) */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="p-3 rounded-xl bg-slate-900/90 border border-indigo-500/20 text-xs">
                      <button
                        onClick={() => toggleSource(msg.id)}
                        className="flex items-center justify-between w-full text-indigo-300 font-semibold hover:text-indigo-200"
                      >
                        <span className="flex items-center gap-1.5">
                          <Bookmark className="w-3.5 h-3.5" />
                          <span>Retrieved Sources ({msg.sources.length} chunks)</span>
                        </span>
                        {expandedSources[msg.id] ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {expandedSources[msg.id] && (
                        <div className="mt-3 space-y-2 border-t border-slate-800 pt-2.5">
                          {msg.sources.map((src, sIdx) => (
                            <div
                              key={sIdx}
                              className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] space-y-1"
                            >
                              <div className="flex items-center justify-between font-medium text-slate-300">
                                <span className="flex items-center gap-1 truncate text-indigo-400">
                                  <FileText className="w-3 h-3" />
                                  {src.document_name || 'Document'}
                                </span>
                                <span className="text-slate-400 font-mono text-[10px]">
                                  Page {src.page_number || 1} {src.cosine_distance !== undefined ? `• Distance: ${src.cosine_distance}` : ''}
                                </span>
                              </div>
                              <p className="text-slate-400 italic font-serif">
                                "{src.snippet}"
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {sending && (
          <div className="flex gap-3 mr-auto max-w-md">
            <div className="w-8 h-8 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-800/90 border border-slate-700/70 rounded-tl-none flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]" />
              <span className="text-xs text-slate-400 ml-2">Retrieving grounded chunks...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Query Input Box */}
      <form onSubmit={handleSend} className="mt-4 relative">
        <div className="relative rounded-2xl bg-slate-900 border border-slate-700/80 shadow-2xl focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all overflow-hidden">
          <textarea
            ref={textareaRef}
            rows={2}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your study materials... (Enter to send, Shift+Enter for new line)"
            className="w-full pl-4 pr-24 py-3 bg-transparent text-slate-100 placeholder-slate-400 text-sm resize-none focus:outline-none"
          />

          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!inputQuery.trim() || sending}
              loading={sending}
              icon={Send}
            >
              Send
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default Chat;
