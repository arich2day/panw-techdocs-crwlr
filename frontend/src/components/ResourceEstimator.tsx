import React from 'react';
import { BudgetStats } from '../types';
import { Cpu, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface ResourceEstimatorProps {
  budget: BudgetStats | null;
}

export const ResourceEstimator: React.FC<ResourceEstimatorProps> = ({ budget }) => {
  if (!budget) return null;

  const slotPercentage = Math.min(100, Math.round((budget.slot_usage_consolidated / budget.max_slots) * 100));
  const wordLimitPct = Math.min(100, Math.round((budget.avg_words_per_target / budget.max_words_per_target) * 100));

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <Cpu size={18} color="#10B981" />
          <span>NotebookLM Resource & Slot Budget</span>
        </div>
        <span className={`panel-badge ${budget.status}`}>
          {budget.status.toUpperCase()}
        </span>
      </div>

      <div className="budget-display">
        {/* Slot Meter */}
        <div className="meter-group">
          <div className="meter-labels">
            <span>NotebookLM Source Slot Usage (Consolidated)</span>
            <span className="value">
              {budget.slot_usage_consolidated} / {budget.max_slots} slots ({slotPercentage}%)
            </span>
          </div>
          <div className="progress-track">
            <div
              className={`progress-bar ${budget.status}`}
              style={{ width: `${slotPercentage}%` }}
            />
          </div>
        </div>

        {/* Word Count Meter per Target Doc */}
        <div className="meter-group">
          <div className="meter-labels">
            <span>Avg Words per Google Doc vs NotebookLM Cap (500k max)</span>
            <span className="value">
              {budget.avg_words_per_target.toLocaleString()} / 500,000 words
            </span>
          </div>
          <div className="progress-track">
            <div
              className="progress-bar optimal"
              style={{ width: `${Math.max(4, wordLimitPct)}%` }}
            />
          </div>
        </div>

        {/* Metric Boxes */}
        <div className="stats-pill-grid">
          <div className="stat-box">
            <span className="label">Matched Docs</span>
            <span className="number">{budget.source_count}</span>
          </div>
          <div className="stat-box">
            <span className="label">Total Words</span>
            <span className="number">{budget.total_words.toLocaleString()}</span>
          </div>
          <div className="stat-box">
            <span className="label">Est. Tokens</span>
            <span className="number">{budget.estimated_tokens.toLocaleString()}</span>
          </div>
        </div>

        {/* Warnings */}
        {budget.warnings.length > 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '0.78rem',
            color: '#FBBF24'
          }}>
            <AlertTriangle size={16} />
            <span>{budget.warnings.join(' • ')}</span>
          </div>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '0.78rem',
            color: '#34D399'
          }}>
            <CheckCircle2 size={16} />
            <span>Optimal sizing: Fits within NotebookLM 50-source slot & word boundaries.</span>
          </div>
        )}
      </div>
    </div>
  );
};
