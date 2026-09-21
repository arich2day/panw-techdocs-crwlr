import React, { useState, useEffect, useRef } from 'react';
import { LogEvent } from '../types';
import { Play, Pause, Trash2, Download, Terminal, Loader2 } from 'lucide-react';

interface TerminalViewerProps {
  logs: LogEvent[];
  isRunning: boolean;
  onClearLogs: () => void;
}

export const TerminalViewer: React.FC<TerminalViewerProps> = ({
  logs,
  isRunning,
  onClearLogs
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleDownloadLogs = () => {
    const text = logs
      .map((l) => `[${l.timestamp}] [${l.level}] ${l.message}`)
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `synclm-pipeline-${new Date().toISOString().slice(0, 10)}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <div className="terminal-title-group">
          <div className="terminal-dots">
            <span className="terminal-dot red" />
            <span className="terminal-dot yellow" />
            <span className="terminal-dot green" />
          </div>
          <div className="terminal-title">
            <span>Pipeline Telemetry & Ingestion Log</span>
            {isRunning && (
              <span style={{ marginLeft: '8px', display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#FA582D' }}>
                <Loader2 size={12} className="animate-spin" />
                <span>SYNCING...</span>
              </span>
            )}
          </div>
        </div>

        <div className="terminal-actions">
          <button
            className={`terminal-btn ${autoScroll ? 'active' : ''}`}
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? 'Auto-scroll is ON' : 'Auto-scroll is PAUSED'}
          >
            {autoScroll ? <Pause size={12} /> : <Play size={12} />}
            <span>{autoScroll ? 'Auto-scroll' : 'Paused'}</span>
          </button>

          <button className="terminal-btn" onClick={handleDownloadLogs} title="Export Log File">
            <Download size={12} />
            <span>Save Log</span>
          </button>

          <button className="terminal-btn" onClick={onClearLogs} title="Clear Terminal">
            <Trash2 size={12} />
            <span>Clear</span>
          </button>
        </div>
      </div>

      <div className="terminal-body" ref={bodyRef}>
        {logs.length === 0 ? (
          <div className="terminal-empty">
            <Terminal size={32} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
            <div>Pipeline idle. Configure options above and click "Trigger Sync Pipeline".</div>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="terminal-line">
              <span className="terminal-timestamp">{log.timestamp}</span>
              <span className={`terminal-pill ${log.level}`}>{log.level}</span>
              <span className="terminal-text">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
