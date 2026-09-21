import React from 'react';
import { Vendor } from '../types';
import { Building2, Check } from 'lucide-react';

interface VendorTogglesProps {
  vendors: Vendor[];
  selectedVendors: string[];
  onToggleVendor: (id: string) => void;
  onSelectPanwOnly: () => void;
  onSelectAllVendors: () => void;
}

export const VendorToggles: React.FC<VendorTogglesProps> = ({
  vendors,
  selectedVendors,
  onToggleVendor,
  onSelectPanwOnly,
  onSelectAllVendors
}) => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <Building2 size={18} color="#FA582D" />
          <span>Vendor Filter & Competitive Landscape</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="terminal-btn" onClick={onSelectPanwOnly}>
            PANW Only
          </button>
          <button className="terminal-btn" onClick={onSelectAllVendors}>
            All Vendors
          </button>
        </div>
      </div>

      <div className="vendor-pills-row">
        {vendors.map((vendor) => {
          const isSelected = selectedVendors.includes(vendor.id);
          return (
            <button
              key={vendor.id}
              className={`vendor-pill ${isSelected ? 'active' : ''} ${!vendor.is_primary ? 'competitor' : ''}`}
              onClick={() => onToggleVendor(vendor.id)}
            >
              {isSelected && <Check size={14} />}
              <span>{vendor.name}</span>
              <span style={{
                fontSize: '0.65rem',
                opacity: 0.75,
                marginLeft: '4px',
                padding: '1px 5px',
                borderRadius: '3px',
                background: vendor.is_primary ? 'rgba(250,88,45,0.2)' : 'rgba(168,85,247,0.2)'
              }}>
                {vendor.badge}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
