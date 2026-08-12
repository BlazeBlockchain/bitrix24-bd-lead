/**
 * BDCapture: On-demand page context extraction and merge policy.
 * fromActiveTab(): injects an extractor function into the page and returns PageContext.
 * merge(): pure function to combine captured data with form values, handling conflicts (FR-007).
 */

/**
 * The extractor function. This MUST be entirely self-contained and serialized into the page.
 * It cannot reference ANY variable from the surrounding module scope.
 * It performs no network calls and must not write to the page.
 */
function pageExtractor() {
  // Company heuristics, in order
  let company = null;

  // 1. og:site_name
  const ogSiteName = document.querySelector('meta[property="og:site_name"]');
  if (ogSiteName) {
    company = ogSiteName.getAttribute('content');
  }

  // 2. application-name
  if (!company) {
    const appName = document.querySelector('meta[name="application-name"]');
    if (appName) {
      company = appName.getAttribute('content');
    }
  }

  // 3. JSON-LD Organization.name
  if (!company) {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (let script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        if (data.name) {
          company = data.name;
          break;
        }
        if (data['@type'] === 'Organization' && data.name) {
          company = data.name;
          break;
        }
      } catch (e) {
        // Ignore malformed JSON-LD
      }
    }
  }

  // 4. hostname fallback (data-model.md: og:site_name -> application-name ->
  // JSON-LD Organization.name -> hostname). Inlined here rather than calling
  // hostnameToCompanyName() because this function is serialized into the
  // page and cannot close over any module-scope helper.
  if (!company) {
    let domain = location.hostname.replace(/^www\./, '').split('.')[0];
    if (domain) {
      company = domain.charAt(0).toUpperCase() + domain.slice(1);
    }
  }

  // Signal heuristics, in order
  let signal = null;

  // 1. User selection (window.getSelection)
  const selection = window.getSelection();
  if (selection && selection.toString()) {
    signal = selection.toString().trim();
  }

  // 2. og:description
  if (!signal) {
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      signal = ogDesc.getAttribute('content');
    }
  }

  // 3. meta[name=description]
  if (!signal) {
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      signal = metaDesc.getAttribute('content');
    }
  }

  // Truncate signal to ~300 chars
  if (signal && signal.length > 300) {
    signal = signal.substring(0, 300).trim() + '…';
  }

  // URL: link[rel=canonical] or location.href
  let url = null;
  const canonical = document.querySelector('link[rel="canonical"]');
  if (canonical) {
    url = canonical.getAttribute('href');
  }
  if (!url) {
    url = location.href;
  }

  // Title
  const title = document.title || null;

  // Selection text (captured separately for reference)
  const selectionText = window.getSelection()
    ? window.getSelection().toString().trim()
    : null;

  return {
    company: company,
    signal: signal,
    url: url,
    title: title,
    selection: selectionText,
  };
}

/**
 * Build an origin match pattern ("https://example.com/*") for a tab URL, or return
 * null when the URL is one Chrome will never let an extension read.
 *
 * Only http/https are permissible: chrome://, chrome-extension://, devtools://,
 * about:, file:// and the Chrome Web Store are all refused by the browser, and
 * tab.url is undefined for tabs we hold no permission over.
 */
function originPatternFor(url) {
  if (!url) return null;
  let parsed;
  try {
    parsed = new URL(url);
  } catch (e) {
    return null;
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
  // Chrome refuses injection into its own Web Store regardless of granted permissions.
  if (/(^|\.)chromewebstore\.google\.com$/.test(parsed.hostname)) return null;
  if (/(^|\.)chrome\.google\.com$/.test(parsed.hostname) && parsed.pathname.startsWith('/webstore')) {
    return null;
  }
  return `${parsed.protocol}//${parsed.hostname}/*`;
}

/**
 * Global BDCapture object exposing page capture and merge logic.
 */
const BDCapture = {
  /**
   * Capture page context from the active tab.
   * Returns { company, signal, title, url, selection }, with any field possibly null.
   * Rejects with { class: 'restricted' } on restricted URLs (chrome://, Web Store, PDF, file://).
   * Resolves with all-null fields when the page yields no usable data.
   */
  async fromActiveTab() {
    // Query the active tab in the current window
    const tabs = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });

    if (!tabs || tabs.length === 0) {
      return { company: null, signal: null, title: null, url: null, selection: null };
    }

    const tab = tabs[0];

    // Ensure we may actually read this page.
    //
    // "activeTab" alone is NOT enough here. Chrome grants activeTab's host access only
    // when the user invokes the extension through the toolbar action, a context-menu
    // item, or a keyboard shortcut. A click on a button INSIDE the side panel is not
    // one of those, so executeScript fails with "Extension manifest must request
    // permission to access the respective host" — verified in a real browser.
    //
    // So we request the origin on demand instead, via optional_host_permissions. This
    // keeps the install-time permission set narrow (NFR-004): the user grants one site
    // at a time, with an explicit Chrome prompt, only when they press the capture button.
    const origin = originPatternFor(tab.url);
    if (!origin) {
      const e = new Error("Can't read this page (unsupported or restricted URL)");
      e.class = 'restricted';
      throw e;
    }

    const alreadyGranted = await chrome.permissions.contains({ origins: [origin] });
    if (!alreadyGranted) {
      // Must be called while the user's click gesture is still live.
      const granted = await chrome.permissions.request({ origins: [origin] });
      if (!granted) {
        const e = new Error(
          `Permission to read ${new URL(tab.url).hostname} was declined. ` +
            'Grant it when prompted, or fill the form in manually.'
        );
        e.class = 'permission';
        throw e;
      }
    }

    // Inject the extractor function
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: pageExtractor,
      });

      if (results && results.length > 0 && results[0].result) {
        return results[0].result;
      }

      // No result
      return { company: null, signal: null, title: null, url: null, selection: null };
    } catch (err) {
      // Restricted URL: chrome://, Web Store, PDF viewer, file:// without permission
      const classError = new Error(
        err.message || "Can't read this page (restricted URL)"
      );
      classError.class = 'restricted';
      throw classError;
    }
  },

  /**
   * Merge captured page context into form values.
   * Pure function: no DOM access, no chrome.* calls, so it is testable.
   * Returns { patch, conflicts }.
   * patch: object with values only for currently-empty fields in formValues.
   * conflicts: array of field names that hold a DIFFERENT non-empty value.
   * Caller confirms before applying conflicts (FR-007).
   */
  merge(pageContext, formValues) {
    const patch = {};
    const conflicts = [];

    // Map page context fields to LeadDraft field names (see data-model.md).
    // `title` is deliberately NOT mapped: the draft has no title field — the caller
    // composes title + url into `notes` instead.
    const fieldMappings = [
      { pageField: 'company', formField: 'company_name' },
      { pageField: 'signal', formField: 'signal' },
      { pageField: 'url', formField: 'source_url' },
    ];

    for (const { pageField, formField } of fieldMappings) {
      const pageValue = pageContext[pageField];
      const formValue = formValues[formField];

      // If pageContext has no value, skip
      if (!pageValue) {
        continue;
      }

      // If form is empty, add to patch
      if (!formValue) {
        patch[formField] = pageValue;
      } else if (formValue !== pageValue) {
        // Form has a different value: flag as conflict
        conflicts.push(formField);
      }
    }

    return { patch, conflicts };
  },
};
