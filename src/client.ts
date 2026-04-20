/**
 * Bitrix24 API client
 * Uses Node.js 18+ native fetch — no axios, no node-fetch.
 */

export interface ContactFields {
  name: string;
  role: string;
  company: string;
}

export interface DealFields {
  title: string;
  contactId: number;
  comments: string;
}

export interface TaskFields {
  title: string;
  description: string;
  deadline: string; // YYYY-MM-DD
  dealId: number;
}

export interface CreatedContact {
  id: number;
}

export interface CreatedDeal {
  id: number;
}

export interface CreatedTask {
  id: number;
}

export class Bitrix24Client {
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

  async createContact(fields: ContactFields): Promise<CreatedContact> {
    const nameParts = fields.name.trim().split(/\s+/);
    const firstName = nameParts[0] ?? fields.name;
    const lastName = nameParts.slice(1).join(' ');

    const id = await this.call<number>('crm.contact.add', {
      fields: {
        NAME: firstName,
        LAST_NAME: lastName,
        POST: fields.role,
        COMPANY_TITLE: fields.company,
      },
    });

    return { id };
  }

  // ─── Deal ─────────────────────────────────────────────────────────────────────

  async createDeal(fields: DealFields): Promise<CreatedDeal> {
    const id = await this.call<number>('crm.deal.add', {
      fields: {
        TITLE: fields.title,
        CONTACT_ID: fields.contactId,
        COMMENTS: fields.comments,
      },
    });

    return { id };
  }

  // ─── Task ─────────────────────────────────────────────────────────────────────

  async createTask(fields: TaskFields): Promise<CreatedTask> {
    // Bitrix24 tasks.task.add returns { task: { id: "123", ... } }
    const result = await this.call<{ task: { id: string } }>('tasks.task.add', {
      fields: {
        TITLE: fields.title,
        DESCRIPTION: fields.description,
        DEADLINE: `${fields.deadline}T09:00:00+00:00`,
        RESPONSIBLE_ID: this.userId,
        UF_CRM_TASK: [`D_${fields.dealId}`],
      },
    });

    return { id: parseInt(result.task.id, 10) };
  }
}
