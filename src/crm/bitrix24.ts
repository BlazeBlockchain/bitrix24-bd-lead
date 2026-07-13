/**
 * Bitrix24 API client implementing CrmClient
 * Uses Node.js 18+ native fetch — no axios, no node-fetch.
 *
 * This is the canonical adapter for Bitrix24.
 * All field mappings, error handling, and call semantics are preserved exactly
 * from the original src/client.ts to ensure 100% backward compatibility for
 * the `bitrix24_create_bd_lead` tool behavior.
 */

import type { CrmClient, CrmContact, CrmDeal, CrmTask } from './types.js';

export class Bitrix24Client implements CrmClient {
  private readonly baseUrl: string;
  private readonly userId: number;

  constructor(webhookUrl: string) {
    // Normalise — remove trailing slash
    this.baseUrl = webhookUrl.replace(/\/+$/, '');
    // Extract user ID from webhook URL: https://domain/rest/{userId}/{token}/
    const match = webhookUrl.match(/\/rest\/(\d+)\//);
    this.userId = match ? parseInt(match[1], 10) : 1;
  }

  // ─── Core HTTP ───────────────────────────────────────────────────────────────

  private async call<T>(method: string, params: Record<string, unknown>): Promise<T> {
    const url = `${this.baseUrl}/${method}.json`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
    } catch (err) {
      throw new Error(`Network error calling Bitrix24 (${method}): ${String(err)}`);
    }

    const body = (await response.json()) as {
      result?: T;
      error?: string;
      error_description?: string;
    };

    if (!response.ok) {
      throw new Error(
        `Bitrix24 HTTP ${response.status} on ${method}: ${body.error ?? response.statusText} — ${body.error_description ?? ''}`
      );
    }

    if (body.error) {
      throw new Error(
        `Bitrix24 API error on ${method}: ${body.error} — ${body.error_description ?? ''}`
      );
    }

    if (body.result === undefined) {
      throw new Error(`Bitrix24 returned no result for ${method}`);
    }

    return body.result;
  }

  // ─── Contact ─────────────────────────────────────────────────────────────────

  async createContact(contact: CrmContact): Promise<{ id: string }> {
    const nameParts = contact.name.trim().split(/\s+/);
    const firstName = nameParts[0] ?? contact.name;
    const lastName = nameParts.slice(1).join(' ');

    const id = await this.call<number>('crm.contact.add', {
      fields: {
        NAME: firstName,
        LAST_NAME: lastName,
        POST: contact.role,
        COMPANY_TITLE: contact.company,
      },
    });

    return { id: String(id) };
  }

  // ─── Deal ─────────────────────────────────────────────────────────────────────

  async createDeal(deal: CrmDeal): Promise<{ id: string }> {
    const id = await this.call<number>('crm.deal.add', {
      fields: {
        TITLE: deal.title,
        // Preserve exact numeric payload shape for CONTACT_ID when possible
        CONTACT_ID: Number(deal.contactId),
        COMMENTS: deal.comments,
      },
    });

    return { id: String(id) };
  }

  // ─── Task ─────────────────────────────────────────────────────────────────────

  // Accept YYYY-MM-DD or full ISO (per CrmClient contract); always return base date for Bitrix.
  // This is defensive for future callers (web, Python backend, HubSpot adapter) while preserving
  // exact current behavior for existing tool.ts (which passes YYYY-MM-DD).
  private normalizeDate(d: string): string {
    return d.includes('T') ? d.split('T')[0] : d;
  }

  async createTask(task: CrmTask): Promise<{ id: string }> {
    // Bitrix24 tasks.task.add returns { task: { id: "123", ... } }
    // Preserve exact field mappings: DEADLINE format, UF_CRM_TASK prefix, RESPONSIBLE_ID
    const result = await this.call<{ task: { id: string } }>('tasks.task.add', {
      fields: {
        TITLE: task.title,
        DESCRIPTION: task.description,
        DEADLINE: `${this.normalizeDate(task.dueDate)}T09:00:00+00:00`,
        RESPONSIBLE_ID: this.userId,
        UF_CRM_TASK: [`D_${task.dealId}`],
      },
    });

    return { id: String(parseInt(result.task.id, 10)) };
  }
}
