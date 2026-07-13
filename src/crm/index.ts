/**
 * CRM barrel exports + minimal provider selector (T002).
 *
 * Re-exports types and adapters for convenient import.
 * Simple factory here for T003 readiness (CRM_PROVIDER selection).
 *
 * Current callers (src/index.ts, src/tool.ts) still import Bitrix directly for
 * 100% back-compat. T003 will wire selection, env, and HubSpot token paths.
 *
 * Usage (future):
 *   import { createCrmClient } from './crm/index.js';
 *   const client = createCrmClient('hubspot', process.env.HUBSPOT_TOKEN!);
 *
 * Source of truth: contracts/crm-client.md + src/crm/types.ts
 */

import type { CrmClient } from './types.js';
import { Bitrix24Client } from './bitrix24.js';
import { HubspotClient } from './hubspot.js';

export * from './types.js';
export { Bitrix24Client } from './bitrix24.js';
export { HubspotClient } from './hubspot.js';

export type CrmProvider = 'bitrix24' | 'hubspot';

/**
 * Minimal factory/selector.
 * config: webhook URL for bitrix24, access token for hubspot.
 * Defaults to bitrix24 for current MCP back-compat (no behavior change).
 */
export function createCrmClient(
  provider: CrmProvider = 'bitrix24',
  config: string
): CrmClient {
  if (provider === 'hubspot') {
    return new HubspotClient(config);
  }
  return new Bitrix24Client(config);
}
