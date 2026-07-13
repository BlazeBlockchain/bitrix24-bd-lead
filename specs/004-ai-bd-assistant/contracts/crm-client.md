# CrmClient Contract

## Interface (shared between web backend, extension, and MCP)

```ts
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
  // healthCheck?(), getProviderName()
}
```

## Bitrix24 Adapter Notes
- Uses existing logic from src/client.ts
- UF_CRM_TASK = [`D_${dealId}`]
- DEADLINE as ISO with time

## HubSpot Adapter Notes
- v3 objects: contacts, deals, tasks
- Associations for linking
- hs_timestamp = due date in ms epoch UTC
