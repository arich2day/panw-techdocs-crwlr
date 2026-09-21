import React from 'react';
import { Technology } from '../types';
import { Network, Globe, Shield, Terminal, Cloud, Check } from 'lucide-react';

interface TechSelectorProps {
  technologies: Technology[];
  selectedTechs: string[];
  onToggleTech: (id: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
}

const getTechIcon = (id: string) => {
  switch (id) {
    case 'sase': return <Network size={18} color="#FA582D" />;
    case 'browser': return <Globe size={18} color="#06B6D4" />;
    case 'ngfw': return <Shield size={18} color="#10B981" />;
    case 'secops': return <Terminal size={18} color="#A855F7" />;
    case 'cloud': return <Cloud size={18} color="#38BDF8" />;
    default: return <Shield size={18} />;
  }
};

export const TechSelector: React.FC<TechSelectorProps> = ({
  technologies,
  selectedTechs,
  onToggleTech,
  onSelectAll,
  onClearAll
}) => {
  const isAllSelected = selectedTechs.length === technologies.length;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <Shield size={18} color="#FA582D" />
          <span>Technology Verticals</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="terminal-btn"
            onClick={isAllSelected ? onClearAll : onSelectAll}
          >
            {isAllSelected ? 'Deselect All' : 'Select All'}
          </button>
          <span className="panel-badge">{selectedTechs.length} Selected</span>
        </div>
      </div>

      <div className="tech-cards-grid">
        {technologies.map((tech) => {
          const isSelected = selectedTechs.includes(tech.id);
          return (
            <div
              key={tech.id}
              className={`tech-card ${isSelected ? 'selected' : ''}`}
              onClick={() => onToggleTech(tech.id)}
            >
              <div className="tech-card-header">
                {getTechIcon(tech.id)}
                {isSelected && (
                  <div style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    backgroundColor: '#FA582D',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Check size={12} color="#FFFFFF" strokeWidth={3} />
                  </div>
                )}
              </div>
              <div className="tech-card-title">{tech.name}</div>
              <div className="tech-card-desc">{tech.description}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
