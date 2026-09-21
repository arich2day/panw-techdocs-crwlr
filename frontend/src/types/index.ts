export interface Technology {
  id: string;
  name: string;
  description: string;
}

export interface Vendor {
  id: string;
  name: string;
  is_primary: boolean;
  badge: string;
}

export interface DocType {
  id: string;
  name: string;
  description: string;
}

export interface DocSource {
  id: string;
  title: string;
  technology: string;
  vendor: string;
  doc_type: string;
  url: string;
  word_estimate: number;
  priority: number;
  description: string;
}

export interface DocTarget {
  id: string;
  name: string;
  technology: string;
  vendor: string;
  google_doc_id: string;
  description: string;
  last_synced?: string | null;
  status: 'verified' | 'unverified' | 'error';
}

export interface BudgetStats {
  source_count: number;
  total_words: number;
  estimated_tokens: number;
  slot_usage_consolidated: number;
  slot_usage_unconsolidated: number;
  max_slots: number;
  avg_words_per_target: number;
  max_words_per_target: number;
  status: 'optimal' | 'warning' | 'danger';
  warnings: string[];
}

export interface LogEvent {
  timestamp: string;
  event_type: 'start' | 'log' | 'source_scraped' | 'doc_synced' | 'complete' | 'error' | 'warn';
  message: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'ERROR';
  data?: Record<string, any>;
}
