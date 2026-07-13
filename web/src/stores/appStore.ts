/**
 * Global app state (Zustand) for web skeleton (T011+).
 * Stub auth (no real JWT), demo CRM selection, local history, last result.
 * Per ARCHITECTURE: Zustand for state. Mirrored patterns for stores.
 */

import { create } from 'zustand';

export type Provider = 'bitrix24' | 'hubspot';

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface PushHistoryItem {
  id: string;
  timestamp: string;
  input: any;
  result: any;
  provider: Provider;
}

interface AppState {
  // Auth stub
  user: User | null;
  isLoggedIn: boolean;
  login: () => void;
  logout: () => void;

  // Demo connections / provider selection (stub for T012)
  currentProvider: Provider;
  demoToken: string; // for ?token= in stub calls
  setProvider: (p: Provider) => void;
  setDemoToken: (t: string) => void;

  // Composer draft (persisted lightly in memory for skeleton)
  draft: {
    company_name: string;
    deal_name: string;
    contact_name: string;
    contact_role: string;
    signal: string;
    pain_point: string;
    notes: string;
  };
  setDraft: (partial: Partial<AppState['draft']>) => void;
  resetDraft: () => void;

  // Results
  lastPushResult: any | null;
  setLastResult: (r: any) => void;

  // Local history stub (T014)
  history: PushHistoryItem[];
  addToHistory: (item: Omit<PushHistoryItem, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
}

const defaultDraft = {
  company_name: '',
  deal_name: '',
  contact_name: '',
  contact_role: '',
  signal: 'Series B announced',
  pain_point: 'Manual follow-ups taking too long',
  notes: '',
};

export const useAppStore = create<AppState>((set) => ({
  user: null,
  isLoggedIn: false,
  login: () => set({
    isLoggedIn: true,
    user: { id: 'demo-user', name: 'Demo BD Rep', email: 'demo@bd.example' }
  }),
  logout: () => set({ isLoggedIn: false, user: null, lastPushResult: null }),

  currentProvider: 'bitrix24',
  demoToken: '',
  setProvider: (p) => set({ currentProvider: p }),
  setDemoToken: (t) => set({ demoToken: t }),

  draft: { ...defaultDraft },
  setDraft: (partial) => set((s) => ({ draft: { ...s.draft, ...partial } })),
  resetDraft: () => set({ draft: { ...defaultDraft } }),

  lastPushResult: null,
  setLastResult: (r) => set({ lastPushResult: r }),

  history: [],
  addToHistory: (item) => {
    const newItem: PushHistoryItem = {
      ...item,
      id: Date.now().toString(36),
      timestamp: new Date().toISOString(),
    };
    set((s) => ({ history: [newItem, ...s.history].slice(0, 20) })); // keep recent
  },
  clearHistory: () => set({ history: [] }),
}));
