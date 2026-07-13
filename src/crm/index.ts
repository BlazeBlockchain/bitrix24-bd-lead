/**
 * CRM barrel exports + provider selector / factory (T003 + T019 MCP wiring).
 *
 * Re-exports types and adapters for convenient import.
 * Full factory supports explicit (provider, config) or env/config resolution.
 *
 * Env support (for MCP and callers):
 * - CRM_PROVIDER=bitrix24|hubspot (default: 'bitrix24')
 * - BITRIX24_WEBHOOK_URL (for bitrix24)
 * - HUBSPOT_ACCESS_TOKEN (for hubspot)
 *
 * Config param takes precedence if provided (non-empty).
 * Defaults to bitrix24 for 100% back-compat with existing MCP / direct usage.
 * No breaking changes: direct Bitrix24Client import/ctor still works.
 *
 * Usage:
 *   import { createCrmClient, CrmProvider } from './crm/index.js';
 *   const client = createCrmClient('hubspot', process.env.HUBSPOT_ACCESS_TOKEN!);
 *   // or env-driven:
 *   const client = createCrmClientFromEnv();
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

/** Supported providers as const for runtime checks / docs. */
export const SUPPORTED_CRM_PROVIDERS: readonly CrmProvider[] = ['bitrix24', 'hubspot'] as const;

/**
 * Resolve config string from env based on provider (if not explicitly passed).
 * Bitrix24: BITRIX24_WEBHOOK_URL
 * HubSpot: HUBSPOT_ACCESS_TOKEN
 */
function resolveConfigFromEnv(provider: CrmProvider): string {
  if (provider === 'hubspot') {
    return process.env.HUBSPOT_ACCESS_TOKEN ?? '';
  }
  return process.env.BITRIX24_WEBHOOK_URL ?? '';
}

/**
 * Full provider selector / factory for CrmClient.
 *
 * @param provider - 'bitrix24' (default) or 'hubspot'
 * @param config - webhook URL or access token. If empty/falsy, resolved from env.
 *                 Config param takes precedence.
 * Returns implementation matching CrmClient exactly (string ids, shapes).
 * Throws on missing config for the selected provider (to preserve old strictness).
 */
export function createCrmClient(
  provider: CrmProvider = 'bitrix24',
  config: string = ''
): CrmClient {
  const resolved = config || resolveConfigFromEnv(provider);
  if (!resolved) {
    const envVar = provider === 'hubspot' ? 'HUBSPOT_ACCESS_TOKEN' : 'BITRIX24_WEBHOOK_URL';
    throw new Error(
      `No config provided for ${provider} and ${envVar} is not set in environment.`
    );
  }
  if (provider === 'hubspot') {
    return new HubspotClient(resolved);
  }
  return new Bitrix24Client(resolved);
}

/**
 * Convenience: create client using CRM_PROVIDER (or default) + matching env config.
 * This is the entrypoint for MCP wiring (T019) and future consumers.
 * Preserves backward compat: if CRM_PROVIDER unset, behaves as bitrix24 + BITRIX24_WEBHOOK_URL.
 */
export function createCrmClientFromEnv(): CrmClient {
  const raw = (process.env.CRM_PROVIDER || 'bitrix24').toLowerCase().trim();
  let provider: CrmProvider;
  if (raw === 'hubspot' || raw === 'hs') {
    provider = 'hubspot';
  } else if (raw === 'bitrix24' || raw === 'bitrix' || raw === '') {
    provider = 'bitrix24';
  } else {
    throw new Error(
      `Unsupported CRM_PROVIDER="${raw}". Supported: bitrix24 | hubspot (default bitrix24 for compat).`
    );
  }
  return createCrmClient(provider);
}
