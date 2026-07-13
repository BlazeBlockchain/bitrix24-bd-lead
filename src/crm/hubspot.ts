/**
 * HubSpot API client implementing CrmClient
 * Uses Node.js 18+ native fetch — no axios, no node-fetch.
 *
 * HubSpot v3 REST specifics (per ARCHITECTURE.md, contracts/crm-client.md, research):
 * - Base: https://api.hubapi.com
 * - Auth: Authorization: Bearer <accessToken> (OAuth or Private App token)
 * - Objects: /crm/v3/objects/contacts , /deals , /tasks
 * - Create with associations (for deal<->contact, task<->deal)
 * - Contact props: firstname, lastname, company, jobtitle (role), email, hs_linkedin_url
 * - Deal props: dealname (title), description (comments), pipeline+dealstage (defaults for v1)
 * - Task props: hs_task_subject, hs_task_body, hs_timestamp (ms epoch UTC), hs_task_status
 * - Associations use HUBSPOT_DEFINED + numeric typeId (3=deal->contact, 216=task->deal)
 * - hs_timestamp: milliseconds since epoch (we use 09:00 UTC on due date to parallel Bitrix)
 *
 * Error handling and {id: string} returns match Bitrix24Client style exactly.
 * IDs from HubSpot are strings.
 *
 * Constructor takes access token (string). (Env/config selection is T003 scope.)
 * No new runtime dependencies.
 */

import type { CrmClient, CrmContact, CrmDeal, CrmTask } from './types.js';

export class HubspotClient implements CrmClient {
  private readonly baseUrl = 'https://api.hubapi.com';

  constructor(private readonly accessToken: string) {
    if (!accessToken || typeof accessToken !== 'string') {
      throw new Error('HubSpot access token is required');
    }
  }

  // ─── Core HTTP ───────────────────────────────────────────────────────────────

  private async call<T>(path: string, body: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
    } catch (err) {
      throw new Error(`Network error calling HubSpot (${path}): ${String(err)}`);
    }

    let bodyJson: any;
    try {
      bodyJson = await response.json();
    } catch {
      bodyJson = {};
    }

    if (!response.ok) {
      const msg = bodyJson.message ?? bodyJson.error ?? response.statusText;
      const corr = bodyJson.correlationId ? ` (corr: ${bodyJson.correlationId})` : '';
      throw new Error(
        `HubSpot HTTP ${response.status} on ${path}: ${msg}${corr}`
      );
    }

    // HubSpot v3 error responses can have status: 'error' even on 200 in some cases
    if (bodyJson && bodyJson.status === 'error') {
      throw new Error(
        `HubSpot API error on ${path}: ${bodyJson.message ?? 'unknown error'}`
      );
    }

    if (bodyJson.id === undefined) {
      // For create, id should be present at top level
      throw new Error(`HubSpot returned no id for ${path}`);
    }

    return bodyJson as T;
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────────

  // Split name like Bitrix24Client (first + rest as last). Defensive.
  private splitName(full: string): { firstname: string; lastname: string } {
    const parts = full.trim().split(/\s+/);
    return {
      firstname: parts[0] ?? full,
      lastname: parts.slice(1).join(' '),
    };
  }

  // Convert YYYY-MM-DD or ISO dueDate to ms-since-epoch UTC.
  // Uses 09:00:00Z to keep consistent semantics with Bitrix DEADLINE T09:00.
  // Per contracts + ARCHITECTURE: hs_timestamp = due ms epoch.
  private toHubspotTimestamp(dueDate: string): number {
    const base = dueDate.includes('T') ? dueDate.split('T')[0] : dueDate;
    // Construct at 09:00 UTC
    const iso = `${base}T09:00:00.000Z`;
    const ts = Date.parse(iso);
    if (isNaN(ts)) {
      // Fallback: treat as already epoch or current (should not happen in normal flow)
      return Date.now();
    }
    return ts;
  }

  // ─── Contact ─────────────────────────────────────────────────────────────────

  async createContact(contact: CrmContact): Promise<{ id: string }> {
    const { firstname, lastname } = this.splitName(contact.name);

    const properties: Record<string, string> = {
      firstname,
      lastname,
      company: contact.company,
    };
    if (contact.role) {
      properties.jobtitle = contact.role;
    }
    if (contact.email) {
      properties.email = contact.email;
    }
    if (contact.linkedin) {
      // hs_linkedin_url is the native HubSpot contact property for LinkedIn profile
      properties.hs_linkedin_url = contact.linkedin;
    }

    // POST /crm/v3/objects/contacts
    // No associations needed at create for contact (deal will link back)
    const result = await this.call<{ id: string }>('/crm/v3/objects/contacts', {
      properties,
    });

    return { id: result.id };
  }

  // ─── Deal ─────────────────────────────────────────────────────────────────────

  async createDeal(deal: CrmDeal): Promise<{ id: string }> {
    const properties: Record<string, string> = {
      dealname: deal.title,
      // description mirrors Bitrix COMMENTS field for the lead context
      description: deal.comments,
      // v1 defaults: use "default" pipeline + first common stage.
      // (Users with custom pipelines may need T003+ config; documented in comments.)
      pipeline: 'default',
      dealstage: 'appointmentscheduled',
    };

    const body = {
      properties,
      // Associate deal -> contact using the standard HUBSPOT_DEFINED type
      // TypeId 3 = Deal to contact (see associations docs + ARCHITECTURE)
      associations: [
        {
          to: { id: deal.contactId },
          types: [
            {
              associationCategory: 'HUBSPOT_DEFINED',
              associationTypeId: 3,
            },
          ],
        },
      ],
    };

    // POST /crm/v3/objects/deals
    const result = await this.call<{ id: string }>('/crm/v3/objects/deals', body);

    return { id: result.id };
  }

  // ─── Task ─────────────────────────────────────────────────────────────────────

  async createTask(task: CrmTask): Promise<{ id: string }> {
    const hsTimestamp = this.toHubspotTimestamp(task.dueDate);

    const properties: Record<string, unknown> = {
      hs_task_subject: task.title,
      hs_task_body: task.description,
      // hs_timestamp in ms since epoch UTC (required; supports number or string)
      hs_timestamp: hsTimestamp,
      hs_task_status: 'NOT_STARTED',
      // hs_task_type omitted (defaults to TODO in HubSpot)
    };

    // Associate task -> deal (216 = Task to deal)
    // We only have dealId in CrmTask (no contactId passed from orchestration).
    // Per task spec "associate to deal+contact if possible": associate to deal here.
    // (Contact association 204 would require extending CrmTask with optional contactId.)
    const associations = [
      {
        to: { id: task.dealId },
        types: [
          {
            associationCategory: 'HUBSPOT_DEFINED',
            associationTypeId: 216,
          },
        ],
      },
    ];

    // POST /crm/v3/objects/tasks
    const result = await this.call<{ id: string }>('/crm/v3/objects/tasks', {
      properties,
      associations,
    });

    return { id: result.id };
  }
}
