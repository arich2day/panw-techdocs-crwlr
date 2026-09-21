import React from 'react';
import { Layers, ShieldCheck, Download } from 'lucide-react';

interface HeaderProps {
  isConfigured: boolean;
  serviceAccountEmail: string | null;
  onOpenExport: () => void;
  onOpenTargets: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  isConfigured,
  serviceAccountEmail,
  onOpenExport,
  onOpenTargets
}) => {
  return (
    <header className="app-header">
      <div className="brand-group">
        <div className="brand-icon-wrapper">
          <Layers size={22} color="#FFFFFF" />
        </div>
        <div className="brand-title-wrap">
          <div className="brand-title">
            <span>SyncLM</span>
            <span className="accent">Studio</span>
            <span className="panel-badge">v1.0</span>
          </div>
          <div className="brand-subtitle">
            Enterprise TechDocs Sync Engine for Google NotebookLM
          </div>
        </div>
      </div>

      <div className="header-status-group">
        <button className="btn btn-secondary" onClick={onOpenTargets}>
          <ShieldCheck size={16} />
          <span>Target Google Docs</span>
        </button>

        <button className="btn btn-outline-cyan" onClick={onOpenExport}>
          <Download size={16} />
          <span>Export Config & CI/CD</span>
        </button>

        <div className="status-pill" title={serviceAccountEmail ? `Service Account: ${serviceAccountEmail}` : 'No Google Cloud credentials detected'}>
          <div className={`status-indicator ${isConfigured ? 'active' : 'warning'}`} />
          <span>{isConfigured ? 'GCP Connected' : 'Dry-Run Mode'}</span>
        </div>
      </div>
    </header>
  );
};
