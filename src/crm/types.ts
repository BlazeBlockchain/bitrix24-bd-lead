/**
 * CrmClient shared interfaces (source of truth per contracts/crm-client.md)
 *
 * These are the canonical types for Bitrix24, HubSpot, and future CRM adapters.
 * Used by MCP server, backend orchestration (T008), web, and extension.
 *
 * DO NOT change without updating the contract and all adapters + callers.
 */

export interface CrmContact {
  name: string;
  role?: string;
  company: string;
  email?: string;
  linkedin?: string;
}

export interface CrmDeal {
  title: string;
  contactId: string;
  comments: string;
}

export interface CrmTask {
  title: string;
  description: string;
  dueDate: string; // YYYY-MM-DD or ISO
  dealId: string;
}

export interface CrmClient {
  createContact(contact: CrmContact): Promise<{ id: string }>;
  createDeal(deal: CrmDeal): Promise<{ id: string }>;
  createTask(task: CrmTask): Promise<{ id: string }>;
  // Future: healthCheck?(), getProviderName?()
}
