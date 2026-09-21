import React, { useState, useEffect, useCallback } from 'react';
import { Technology, Vendor, DocType, DocSource, DocTarget, BudgetStats, LogEvent } from './types';
import { Header } from './components/Header';
import { TechSelector } from './components/TechSelector';
import { VendorToggles } from './components/VendorToggles';
import { DocTypeSelector } from './components/DocTypeSelector';
import { ResourceEstimator } from './components/ResourceEstimator';
import { TerminalViewer } from './components/TerminalViewer';
import { TargetManager } from './components/TargetManager';
import { ConfigExportModal } from './components/ConfigExportModal';
import { Play, Database } from 'lucide-react';

export const App: React.FC = () => {
  // Metadata state
  const [technologies, setTechnologies] = useState<Technology[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [docTypes, setDocTypes] = useState<DocType[]>([]);
  const [allSources, setAllSources] = useState<DocSource[]>([]);
  const [targets, setTargets] = useState<DocTarget[]>([]);
  const [isConfigured, setIsConfigured] = useState<boolean>(false);
  const [serviceAccountEmail, setServiceAccountEmail] = useState<string | null>(null);

  // Filter selections
  const [selectedTechs, setSelectedTechs] = useState<string[]>(['sase', 'browser', 'ngfw']);
  const [selectedVendors, setSelectedVendors] = useState<string[]>(['panw', 'zscaler', 'island']);
  const [selectedDocTypes, setSelectedDocTypes] = useState<string[]>([
    'architecture',
    'release_notes',
    'api_specs',
    'battlecards'
  ]);
  const [dryRun, setDryRun] = useState<boolean>(true);

  // Budget & Telemetry
  const [budget, setBudget] = useState<BudgetStats | null>(null);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  // Modal dialogs
  const [isTargetModalOpen, setIsTargetModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // 1. Initial Load: Fetch metadata & health
  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((data) => {
        setIsConfigured(data.gdocs_configured);
        setServiceAccountEmail(data.service_account_email);
      })
      .catch(() => setIsConfigured(false));

    fetch('/api/metadata')
      .then((r) => r.json())
      .then((data) => {
        setTechnologies(data.technologies || []);
        setVendors(data.vendors || []);
        setDocTypes(data.doc_types || []);
      });

    fetch('/api/sources')
      .then((r) => r.json())
      .then((data) => setAllSources(data || []));

    fetch('/api/targets')
      .then((r) => r.json())
      .then((data) => setTargets(data || []));
  }, []);

  // 2. Dynamic Budget Calculation
  const recomputeBudget = useCallback(() => {
    fetch('/api/budget', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        technologies: selectedTechs,
        vendors: selectedVendors,
        doc_types: selectedDocTypes
      })
    })
      .then((r) => r.json())
      .then((data) => setBudget(data))
      .catch((err) => console.error('Budget error:', err));
  }, [selectedTechs, selectedVendors, selectedDocTypes]);

  useEffect(() => {
    recomputeBudget();
  }, [recomputeBudget]);

  // 3. SSE Log Stream Connection
  useEffect(() => {
    const eventSource = new EventSource('/api/sync/stream');

    eventSource.onmessage = (event) => {
      try {
        const parsed: LogEvent = JSON.parse(event.data);
        setLogs((prev) => [...prev, parsed]);
        if (parsed.event_type === 'start') {
          setIsRunning(true);
        } else if (parsed.event_type === 'complete' || parsed.event_type === 'error') {
          setIsRunning(false);
        }
      } catch (e) {
        console.error('SSE parse error:', e);
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Filter handlers
  const handleToggleTech = (id: string) => {
    setSelectedTechs((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const handleToggleVendor = (id: string) => {
    setSelectedVendors((prev) =>
      prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]
    );
  };

  const handleToggleDocType = (id: string) => {
    setSelectedDocTypes((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  // Filtered source list
  const filteredSources = allSources.filter(
    (s) =>
      selectedTechs.includes(s.technology) &&
      selectedVendors.includes(s.vendor) &&
      selectedDocTypes.includes(s.doc_type)
  );

  // Trigger Sync Pipeline
  const handleTriggerSync = async () => {
    if (isRunning) return;
    setIsRunning(true);

    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          technologies: selectedTechs,
          vendors: selectedVendors,
          doc_types: selectedDocTypes,
          dry_run: dryRun
        })
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`Error starting pipeline: ${err.detail || 'Unknown error'}`);
        setIsRunning(false);
      }
    } catch (err: any) {
      alert(`Network error starting pipeline: ${err.message}`);
      setIsRunning(false);
    }
  };

  // Target operations
  const handleSaveTarget = async (target: Partial<DocTarget>) => {
    await fetch('/api/targets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(target)
    });
    const refreshed = await (await fetch('/api/targets')).json();
    setTargets(refreshed);
  };

  const handleDeleteTarget = async (id: string) => {
    await fetch(`/api/targets/${id}`, { method: 'DELETE' });
    setTargets((prev) => prev.filter((t) => t.id !== id));
  };

  const handleTestTarget = async (googleDocId: string) => {
    const res = await fetch('/api/targets/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ google_doc_id: googleDocId })
    });
    return res.json();
  };

  return (
    <div className="app-container">
      <Header
        isConfigured={isConfigured}
        serviceAccountEmail={serviceAccountEmail}
        onOpenExport={() => setIsExportModalOpen(true)}
        onOpenTargets={() => setIsTargetModalOpen(true)}
      />

      <main className="main-content">
        <div className="studio-grid">
          {/* Left Column: Filter & Builder Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <TechSelector
              technologies={technologies}
              selectedTechs={selectedTechs}
              onToggleTech={handleToggleTech}
              onSelectAll={() => setSelectedTechs(technologies.map((t) => t.id))}
              onClearAll={() => setSelectedTechs([])}
            />

            <VendorToggles
              vendors={vendors}
              selectedVendors={selectedVendors}
              onToggleVendor={handleToggleVendor}
              onSelectPanwOnly={() => setSelectedVendors(['panw'])}
              onSelectAllVendors={() => setSelectedVendors(vendors.map((v) => v.id))}
            />

            <DocTypeSelector
              docTypes={docTypes}
              selectedDocTypes={selectedDocTypes}
              onToggleDocType={handleToggleDocType}
            />

            {/* Action & Trigger Bar */}
            <div className="panel">
              <div className="action-bar">
                <div className="mode-toggle-group">
                  <label className="switch-label">
                    <input
                      type="checkbox"
                      checked={dryRun}
                      onChange={(e) => setDryRun(e.target.checked)}
                      style={{ cursor: 'pointer', accentColor: '#FA582D', width: '16px', height: '16px' }}
                    />
                    <span>Dry-Run Simulation Mode</span>
                  </label>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    (Simulates scraping & deduplication without Google Docs API writes)
                  </span>
                </div>

                <button
                  className="btn btn-primary"
                  onClick={handleTriggerSync}
                  disabled={isRunning || filteredSources.length === 0}
                >
                  <Play size={16} />
                  <span>{isRunning ? 'Pipeline Executing...' : 'Trigger Sync Pipeline'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Resource Estimator & Live Terminal */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <ResourceEstimator budget={budget} />

            <div className="panel" style={{ padding: '0', background: 'transparent', border: 'none' }}>
              <TerminalViewer
                logs={logs}
                isRunning={isRunning}
                onClearLogs={() => setLogs([])}
              />
            </div>

            {/* Matched Sources Quick Inspection Card */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">
                  <Database size={18} color="#FA582D" />
                  <span>Active Ingestion Sources</span>
                </div>
                <span className="panel-badge">{filteredSources.length} Matched</span>
              </div>
              <div style={{ maxHeight: '200px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {filteredSources.map((s) => (
                  <div
                    key={s.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.78rem',
                      padding: '6px 10px',
                      backgroundColor: 'var(--bg-card)',
                      borderRadius: '4px',
                      border: '1px solid var(--border-subtle)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="panel-badge" style={{ textTransform: 'uppercase', fontSize: '0.65rem' }}>
                        {s.vendor}
                      </span>
                      <span style={{ fontWeight: 500 }}>{s.title}</span>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      ~{s.word_estimate.toLocaleString()} words
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Target Manager Modal */}
      <TargetManager
        isOpen={isTargetModalOpen}
        onClose={() => setIsTargetModalOpen(false)}
        targets={targets}
        technologies={technologies}
        onSaveTarget={handleSaveTarget}
        onDeleteTarget={handleDeleteTarget}
        onTestTarget={handleTestTarget}
      />

      {/* Config Exporter Modal */}
      <ConfigExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        filteredSources={filteredSources}
        selectedTechs={selectedTechs}
        selectedVendors={selectedVendors}
      />
    </div>
  );
};
