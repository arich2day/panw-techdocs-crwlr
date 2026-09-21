import React, { useState } from 'react';
import { DocTarget, Technology } from '../types';
import { X, CheckCircle2, AlertCircle, RefreshCw, Plus, ExternalLink, Trash2 } from 'lucide-react';

interface TargetManagerProps {
  isOpen: boolean;
  onClose: () => void;
  targets: DocTarget[];
  technologies: Technology[];
  onSaveTarget: (target: Partial<DocTarget>) => Promise<void>;
  onDeleteTarget: (targetId: string) => Promise<void>;
  onTestTarget: (googleDocId: string) => Promise<any>;
}

export const TargetManager: React.FC<TargetManagerProps> = ({
  isOpen,
  onClose,
  targets,
  technologies,
  onSaveTarget,
  onDeleteTarget,
  onTestTarget
}) => {
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, any>>({});
  const [editingTarget, setEditingTarget] = useState<Partial<DocTarget> | null>(null);

  if (!isOpen) return null;

  const handleTest = async (docId: string) => {
    setTestingId(docId);
    try {
      const res = await onTestTarget(docId);
      setTestResult((prev) => ({ ...prev, [docId]: res }));
    } catch (e: any) {
      setTestResult((prev) => ({ ...prev, [docId]: { accessible: false, error: e.message } }));
    } finally {
      setTestingId(null);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingTarget) {
      await onSaveTarget(editingTarget);
      setEditingTarget(null);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '780px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="panel-title">
            <span>Google Doc Target Configuration</span>
            <span className="panel-badge">{targets.length} Registered</span>
          </div>
          <button className="terminal-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Each target corresponds to one Google Doc where scraped Markdown is batch-synchronized.
            NotebookLM can ingest up to 50 target docs.
          </p>

          {/* List of Targets */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {targets.map((t) => {
              const test = testResult[t.google_doc_id];
              return (
                <div
                  key={t.id}
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>{t.name}</span>
                      <span className="panel-badge" style={{ textTransform: 'uppercase' }}>
                        {t.technology}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button
                        className="terminal-btn"
                        onClick={() => handleTest(t.google_doc_id)}
                        disabled={testingId === t.google_doc_id}
                      >
                        <RefreshCw size={12} className={testingId === t.google_doc_id ? 'animate-spin' : ''} />
                        <span>Test Link</span>
                      </button>

                      <a
                        href={`https://docs.google.com/document/d/${t.google_doc_id}/edit`}
                        target="_blank"
                        rel="noreferrer"
                        className="terminal-btn"
                      >
                        <ExternalLink size={12} />
                      </a>

                      <button
                        className="terminal-btn"
                        onClick={() => onDeleteTarget(t.id)}
                        style={{ color: '#F87171' }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Doc ID:</span>
                    <code style={{ color: '#38BDF8', fontFamily: 'var(--font-mono)' }}>
                      {t.google_doc_id}
                    </code>
                  </div>

                  {test && (
                    <div
                      style={{
                        padding: '6px 10px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        backgroundColor: test.accessible ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: test.accessible ? '#34D399' : '#F87171',
                        border: `1px solid ${test.accessible ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                      }}
                    >
                      {test.accessible ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <CheckCircle2 size={14} />
                          <span>Connected: "{test.title}"</span>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <AlertCircle size={14} />
                          <span>{test.error}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Add or Edit Target Form */}
          <div style={{
            marginTop: '12px',
            padding: '14px',
            backgroundColor: 'var(--bg-panel)',
            border: '1px dashed var(--border-hover)',
            borderRadius: '8px'
          }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14} color="#FA582D" />
              <span>Register / Update Google Doc Target</span>
            </h4>
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <input
                  type="text"
                  placeholder="Target Name (e.g. SASE Architecture)"
                  className="input-text"
                  required
                  value={editingTarget?.name || ''}
                  onChange={(e) => setEditingTarget((prev) => ({ ...prev, name: e.target.value }))}
                />
                <select
                  className="input-text"
                  value={editingTarget?.technology || 'sase'}
                  onChange={(e) => setEditingTarget((prev) => ({ ...prev, technology: e.target.value }))}
                >
                  {technologies.map((tech) => (
                    <option key={tech.id} value={tech.id}>
                      {tech.name}
                    </option>
                  ))}
                </select>
              </div>
              <input
                type="text"
                placeholder="Google Doc ID (from docs.google.com/document/d/<ID>/edit)"
                className="input-text"
                required
                value={editingTarget?.google_doc_id || ''}
                onChange={(e) => setEditingTarget((prev) => ({ ...prev, google_doc_id: e.target.value }))}
              />
              <button type="submit" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>
                Save Target
              </button>
            </form>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
