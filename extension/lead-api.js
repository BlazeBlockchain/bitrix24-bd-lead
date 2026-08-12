/**
 * BDApi: Sole owner of the lead request/response contracts.
 * Centralises the LeadPushInput shape (copied verbatim from popup.js:55-67) and error classification.
 * Every method rejects with { class, message } per contracts/api-contracts.md (FR-014, NFR-002).
 */

/**
 * Build the lead input from form data (matches LeadPushInput shape).
 * Copied verbatim from extension/popup.js:55-67, including the placeholder guards
 * ('Acme Corp', `${company} Intro Deal`, 'Jane Doe', 'Head of Growth', signal_type 'new_launch',
 * `Intro to ${company}`) and the || undefined omission of empty optionals.
 * This shape is FROZEN — backend tests and the web app depend on it.
 */
function buildLeadInput(formValues) {
  // Assume formValues has company_name, contact_name, contact_role, signal, pain_point, notes
  return {
    company_name: formValues.company_name || 'Acme Corp',
    deal_name: `${formValues.company_name || 'Acme'} Intro Deal`,
    contact_name: formValues.contact_name || 'Jane Doe',
    contact_role: formValues.contact_role || 'Head of Growth',
    signal: formValues.signal || undefined,
    signal_type: 'new_launch',
    pain_point: formValues.pain_point || undefined,
    email_subject: `Intro to ${formValues.company_name || 'Acme'}`,
    notes: formValues.notes || undefined,
  };
}

/**
 * Classify network and HTTP errors into the contract categories.
 */
function classifyError(fetchError, httpStatus, serverDetail) {
  if (fetchError) {
    return { class: 'unreachable', message: "Can't reach the BD Lead service" };
  }
  if (httpStatus === 401) {
    return { class: 'session', message: 'Signed out or session expired' };
  }
  if (httpStatus === 422) {
    return { class: 'input', message: serverDetail || 'Invalid request' };
  }
  return {
    class: 'service',
    message: serverDetail || `Server error (${httpStatus})`,
  };
}

/**
 * Global BDApi object exposing enrich, push, health, and buildInput.
 */
const BDApi = {
  /**
   * Build the LeadPushInput from form values.
   */
  buildInput(formValues) {
    return buildLeadInput(formValues);
  },

  /**
   * POST /api/leads/enrich to generate the preview.
   * Requires a valid session (throws 'session' error if absent/expired).
   * Rejects with { class, message } on any error.
   */
  async enrich(input) {
    let authHeaders;
    try {
      authHeaders = await BDAuth.authHeaders();
    } catch (err) {
      // BDAuth.authHeaders throws with class 'session'
      throw err;
    }

    try {
      const response = await fetch(`${API_BASE}/leads/enrich`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify(input),
      });

      if (!response.ok) {
        const serverError = await response.json().catch(() => ({}));
        const classified = classifyError(
          false,
          response.status,
          serverError.detail
        );
        const err = new Error(classified.message);
        err.class = classified.class;
        throw err;
      }

      return await response.json();
    } catch (err) {
      // If already classified, rethrow
      if (err.class) {
        throw err;
      }
      // Network error
      const classError = new Error(
        err.message || "Can't reach the BD Lead service"
      );
      classError.class = 'unreachable';
      throw classError;
    }
  },

  /**
   * POST /api/leads/push?provider=<encoded> to create the lead in the CRM.
   * Requires a valid session (throws 'session' error if absent/expired).
   * Rejects with { class, message } on any error.
   */
  async push(input, provider) {
    let authHeaders;
    try {
      authHeaders = await BDAuth.authHeaders();
    } catch (err) {
      // BDAuth.authHeaders throws with class 'session'
      throw err;
    }

    try {
      const url = `${API_BASE}/leads/push?provider=${encodeURIComponent(provider)}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify(input),
      });

      if (!response.ok) {
        const serverError = await response.json().catch(() => ({}));
        const classified = classifyError(
          false,
          response.status,
          serverError.detail
        );
        const err = new Error(classified.message);
        err.class = classified.class;
        throw err;
      }

      return await response.json();
    } catch (err) {
      // If already classified, rethrow
      if (err.class) {
        throw err;
      }
      // Network error
      const classError = new Error(
        err.message || "Can't reach the BD Lead service"
      );
      classError.class = 'unreachable';
      throw classError;
    }
  },

  /**
   * HEAD /api/health to check if the backend is reachable.
   * Never throws; always resolves to a boolean.
   */
  async health() {
    try {
      const response = await fetch(`${API_BASE}/health`, { method: 'HEAD' });
      return response.ok;
    } catch (err) {
      // Network error or timeout
      return false;
    }
  },
};
