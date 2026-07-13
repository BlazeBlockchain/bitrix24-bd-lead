/**
 * bitrix24_create_bd_lead
 * Receives output from the B2B Sales Research Skill and creates
 * a Contact, Deal, and 3 Follow-up Tasks in Bitrix24.
 */

import { z } from 'zod';
import type { CrmClient } from './crm/types.js';

// ─── Input schema ─────────────────────────────────────────────────────────────

export const BdLeadSchema = z.object({
  company_name: z.string().min(1),
  deal_name: z.string().min(1),
  signal: z.string().min(1),
  signal_type: z.enum([
    'new_leadership',
    'funding',
    'hiring_gap',
    'outdated_site',
    'new_launch',
    'negative_reviews',
  ]),
  contact_name: z.string().min(1),
  contact_role: z.string().min(1),
  pain_point: z.string().min(1),
  email_subject: z.string().min(1),
  notes: z.string().min(1),
});

export type BdLeadInput = z.infer<typeof BdLeadSchema>;

// ─── MCP tool definition (JSON Schema for MCP protocol) ───────────────────────

export const BD_LEAD_TOOL = {
  name: 'bitrix24_create_bd_lead',
  description:
    'Creates a Contact, Deal, and 3 Follow-up Tasks in Bitrix24 from a B2B Sales Research Lead Brief. ' +
    'Use this after generating a Lead Brief with the B2B Sales Research Skill.',
  inputSchema: {
    type: 'object',
    properties: {
      company_name: {
        type: 'string',
        description: 'Company name, e.g. "Infobip"',
      },
      deal_name: {
        type: 'string',
        description: 'Deal name in format "[Company] — [Signal in 3 words]", e.g. "Infobip — AgentOS Launch Window"',
      },
      signal: {
        type: 'string',
        description: 'What buying signal was found and where, e.g. "AgentOS product launch announced Feb 26, official release April 1"',
      },
      signal_type: {
        type: 'string',
        enum: ['new_leadership', 'funding', 'hiring_gap', 'outdated_site', 'new_launch', 'negative_reviews'],
        description: 'Category of the buying signal',
      },
      contact_name: {
        type: 'string',
        description: 'Decision maker full name, or "Head of Marketing" if unknown',
      },
      contact_role: {
        type: 'string',
        description: 'Decision maker title, e.g. "Chief Innovation Officer" or "Decision Maker — Unknown"',
      },
      pain_point: {
        type: 'string',
        description: 'Why this signal matters to them right now',
      },
      email_subject: {
        type: 'string',
        description: 'Cold email subject line (max 8 words)',
      },
      notes: {
        type: 'string',
        description: 'Max 3 bullet points of key context before a call',
      },
    },
    required: [
      'company_name',
      'deal_name',
      'signal',
      'signal_type',
      'contact_name',
      'contact_role',
      'pain_point',
      'email_subject',
      'notes',
    ],
  },
} as const;

// ─── Date helpers ─────────────────────────────────────────────────────────────

function addDays(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

// ─── Task descriptions ────────────────────────────────────────────────────────

function task1Description(contactName: string, companyName: string): string {
  return (
    `Check if email was opened. Connect on LinkedIn with this note (max 300 chars):\n\n` +
    `"Hi ${contactName} — sent you a note about ${companyName} earlier this week. ` +
    `Thought it was worth connecting directly too."\n\n` +
    `If no open: resend with a different subject line using the same signal.`
  );
}

function task2Description(
  signalType: BdLeadInput['signal_type'],
  companyName: string
): string {
  const map: Record<BdLeadInput['signal_type'], string> = {
    new_leadership:
      `Reply to original thread. One line only:\n\n` +
      `"Any chance this landed at a bad time? Happy to share what we did for [similar client] — ` +
      `took them from [problem] to [result] in 8 weeks."`,
    funding:
      `Reply to original thread. One line only:\n\n` +
      `"Still relevant? Most teams in your position find the window closes faster than expected."`,
    hiring_gap:
      `Reply to original thread. One line only:\n\n` +
      `"Still building the team? We've bridged this gap for a few companies lately — ` +
      `might be worth 15 minutes."`,
    outdated_site:
      `Reply to original thread. One line only:\n\n` +
      `"Did this land? The site issue is costing ${companyName} leads every week it stays."`,
    new_launch:
      `Reply to original thread. One line only:\n\n` +
      `"Launch window getting closer? Happy to show you what worked for [client]."`,
    negative_reviews:
      `Reply to original thread. One line only:\n\n` +
      `"Still relevant? Every day this stays public it costs you leads."`,
  };
  return map[signalType];
}

function task3Description(painPoint: string): string {
  return (
    `Final email. Keep it short. Leave the door open. Never guilt-trip.\n\n` +
    `"Last note from me on this — if timing is off, no problem at all. ` +
    `If ${painPoint} becomes a priority, you know where to find us."`
  );
}

// ─── Execution ────────────────────────────────────────────────────────────────

/**
 * Result IDs are strings (per CrmClient contract for portability across CRMs, JSON, Python backend, and web/extension).
 * The MCP tool output formatting and observable behavior remain unchanged.
 */
export interface BdLeadResult {
  contact_id: string;
  deal_id: string;
  task1: { id: string; date: string };
  task2: { id: string; date: string };
  task3: { id: string; date: string };
}

export async function executeBdLead(
  input: BdLeadInput,
  client: CrmClient
): Promise<BdLeadResult> {
  // 1 — Contact
  const contact = await client.createContact({
    name: input.contact_name,
    role: input.contact_role,
    company: input.company_name,
  });

  // 2 — Deal
  const dealComments =
    `Signal: ${input.signal}\n\n` +
    `Pain Point: ${input.pain_point}\n\n` +
    `Email Subject: ${input.email_subject}\n\n` +
    `Notes:\n${input.notes}`;

  const deal = await client.createDeal({
    title: input.deal_name,
    contactId: contact.id,
    comments: dealComments,
  });

  // 3 — Tasks
  const date1 = addDays(4);
  const date2 = addDays(9);
  const date3 = addDays(14);

  const task1 = await client.createTask({
    title: 'Follow-up 1 — Check + Connect',
    description: task1Description(input.contact_name, input.company_name),
    dueDate: date1,
    dealId: deal.id,
  });

  const task2 = await client.createTask({
    title: 'Follow-up 2 — Short Bump',
    description: task2Description(input.signal_type, input.company_name),
    dueDate: date2,
    dealId: deal.id,
  });

  const task3 = await client.createTask({
    title: 'Follow-up 3 — Close the Loop',
    description: task3Description(input.pain_point),
    dueDate: date3,
    dealId: deal.id,
  });

  return {
    contact_id: contact.id,
    deal_id: deal.id,
    task1: { id: task1.id, date: date1 },
    task2: { id: task2.id, date: date2 },
    task3: { id: task3.id, date: date3 },
  };
}
