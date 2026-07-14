/**
 * Global app state (Zustand) for web.
 * Real Google OAuth + JWT auth (per review Tier 1).
 */

import { create } from 'zustand';
import type { AuthUser } from '../api/auth';
import { clearStoredAuth } from '../api/auth';

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
  // Real auth (Google OAuth + JWT)
  user: User | null;
  accessToken: string | null;
  isLoggedIn: boolean;
  setAuthFromToken: (token: string, authUser: AuthUser) => void;
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

  // History (T014): local for immediate post-push; server via getHistory in component. Shared shape for use-similar.
  history: PushHistoryItem[];
  addToHistory: (item: Omit<PushHistoryItem, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  // For server history items (from /api/leads/history) which have different shape (id, company_name etc + enriched)
  serverHistory: any[];
  setServerHistory: (items: any[]) => void;
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
  accessToken: null,
  isLoggedIn: false,
  setAuthFromToken: (token: string, authUser: AuthUser) => set({
    isLoggedIn: true,
    accessToken: token,
    user: {
      id: authUser.id,
      name: authUser.display_name,
      email: authUser.email,
    },
  }),
  logout: () => {
    clearStoredAuth();
    set({ isLoggedIn: false, accessToken: null, user: null, lastPushResult: null });
  },

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

  serverHistory: [],
  setServerHistory: (items) => set({ serverHistory: items }),
}));
