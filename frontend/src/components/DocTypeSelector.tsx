import React from 'react';
import { DocType } from '../types';
import { FileText, Check } from 'lucide-react';

interface DocTypeSelectorProps {
  docTypes: DocType[];
  selectedDocTypes: string[];
  onToggleDocType: (id: string) => void;
}

export const DocTypeSelector: React.FC<DocTypeSelectorProps> = ({
  docTypes,
  selectedDocTypes,
  onToggleDocType
}) => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <FileText size={18} color="#06B6D4" />
          <span>Documentation Content Types</span>
        </div>
        <span className="panel-badge">{selectedDocTypes.length} Active</span>
      </div>

      <div className="doc-type-grid">
        {docTypes.map((dt) => {
          const isSelected = selectedDocTypes.includes(dt.id);
          return (
            <div
              key={dt.id}
              className={`doc-type-item ${isSelected ? 'selected' : ''}`}
              onClick={() => onToggleDocType(dt.id)}
            >
              <div className="checkbox-box">
                {isSelected && <Check size={12} color="#FFFFFF" strokeWidth={3} />}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {dt.name}
                </span>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {dt.description}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
