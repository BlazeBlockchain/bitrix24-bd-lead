/**
 * Type declarations for Google Identity Services (GIS).
 * Loaded from https://accounts.google.com/gsi/client
 */

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string;
    callback: (response: { credential: string }) => void;
    cancel_on_tap_outside?: boolean;
    [key: string]: unknown;
  }) => void;
  renderButton: (
    element: HTMLElement,
    options: {
      type?: string;
      shape?: string;
      theme?: string;
      size?: string;
      text?: string;
      width?: number;
      [key: string]: unknown;
    }
  ) => void;
  prompt: () => void;
}

interface GoogleAccounts {
  id: GoogleAccountsId;
}

interface Google {
  accounts: GoogleAccounts;
}

declare const google: Google;
