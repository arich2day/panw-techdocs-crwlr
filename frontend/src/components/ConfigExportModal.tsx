import React, { useState } from 'react';
import { DocSource } from '../types';
import { X, Copy, Check, FileCode } from 'lucide-react';

interface ConfigExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  filteredSources: DocSource[];
  selectedTechs: string[];
  selectedVendors: string[];
}

export const ConfigExportModal: React.FC<ConfigExportModalProps> = ({
  isOpen,
  onClose,
  filteredSources,
  selectedTechs,
  selectedVendors
}) => {
  const [activeTab, setActiveTab] = useState<'json' | 'github' | 'cli'>('json');
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const jsonExport = JSON.stringify(filteredSources, null, 2);

  const cliCommand = `python scripts/run_sync.py --tech ${selectedTechs.join(',') || 'all'} --vendor ${selectedVendors.join(',') || 'all'} --dry-run`;

  const githubYaml = `name: SyncLM TechDocs Automated Pipeline

on:
  schedule:
    - cron: '0 4 * * 1' # Weekly Monday at 04:00 UTC
  workflow_dispatch:
    inputs:
      technology:
        description: 'Technology Vertical'
        default: '${selectedTechs[0] || 'all'}'
      vendor:
        description: 'Vendor Filter'
        default: '${selectedVendors[0] || 'all'}'
      dry_run:
        default: false
        type: boolean

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - name: Run SyncLM Pipeline
        env:
          GCP_SA_KEY_B64: \${{ secrets.GCP_SA_KEY_B64 }}
        run: |
          python scripts/run_sync.py \\
            --tech "\${{ github.event.inputs.technology }}" \\
            --vendor "\${{ github.event.inputs.vendor }}"
`;

  const currentContent = activeTab === 'json' ? jsonExport : activeTab === 'github' ? githubYaml : cliCommand;

  const handleCopy = () => {
    navigator.clipboard.writeText(currentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="panel-title">
            <FileCode size={18} color="#FA582D" />
            <span>Config & Pipeline Exporter</span>
          </div>
          <button className="terminal-btn" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body">
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <button
              className={`terminal-btn ${activeTab === 'json' ? 'active' : ''}`}
              onClick={() => setActiveTab('json')}
            >
              doc_sources.json ({filteredSources.length} items)
            </button>
            <button
              className={`terminal-btn ${activeTab === 'github' ? 'active' : ''}`}
              onClick={() => setActiveTab('github')}
            >
              sync-docs.yml (GitHub Action)
            </button>
            <button
              className={`terminal-btn ${activeTab === 'cli' ? 'active' : ''}`}
              onClick={() => setActiveTab('cli')}
            >
              CLI Invocation
            </button>
          </div>

          <pre className="code-preview">{currentContent}</pre>
        </div>

        <div className="modal-footer">
          <button className="btn btn-primary" onClick={handleCopy}>
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? 'Copied to Clipboard!' : 'Copy to Clipboard'}</span>
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
