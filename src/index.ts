/**
 * Bitrix24 BD Lead — MCP Server
 * Exposes one tool: bitrix24_create_bd_lead
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { Bitrix24Client } from './crm/bitrix24.js';
import { BD_LEAD_TOOL, BdLeadSchema, executeBdLead } from './tool.js';

// ─── Config ───────────────────────────────────────────────────────────────────

const webhookUrl = process.env['BITRIX24_WEBHOOK_URL'];
if (!webhookUrl) {
  process.stderr.write(
    'ERROR: BITRIX24_WEBHOOK_URL is not set.\n' +
    'Copy .env.example to .env and add your webhook URL.\n'
  );
  process.exit(1);
}

// Basic URL format check
try {
  new URL(webhookUrl);
} catch {
  process.stderr.write(`ERROR: BITRIX24_WEBHOOK_URL is not a valid URL: ${webhookUrl}\n`);
  process.exit(1);
}

const client = new Bitrix24Client(webhookUrl);

// ─── MCP Server ───────────────────────────────────────────────────────────────

const server = new Server(
  { name: 'bitrix24-bd-lead', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [BD_LEAD_TOOL],
}));

// Execute tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== 'bitrix24_create_bd_lead') {
    return {
      content: [{ type: 'text', text: `Unknown tool: ${request.params.name}` }],
      isError: true,
    };
  }

  // Validate input with Zod
  const parsed = BdLeadSchema.safeParse(request.params.arguments);
  if (!parsed.success) {
    const issues = parsed.error.issues
      .map((i) => `  • ${i.path.join('.')}: ${i.message}`)
      .join('\n');
    return {
      content: [{ type: 'text', text: `Invalid input:\n${issues}` }],
      isError: true,
    };
  }

  try {
    const result = await executeBdLead(parsed.data, client);

    const output = [
      '✅ Bitrix24 entry created successfully',
      '',
      `Contact ID : ${result.contact_id}`,
      `Deal ID    : ${result.deal_id}`,
      '',
      `Task 1 ID  : ${result.task1.id}  →  Follow-up 1 — Check + Connect  (${result.task1.date})`,
      `Task 2 ID  : ${result.task2.id}  →  Follow-up 2 — Short Bump       (${result.task2.date})`,
      `Task 3 ID  : ${result.task3.id}  →  Follow-up 3 — Close the Loop   (${result.task3.date})`,
    ].join('\n');

    return {
      content: [{ type: 'text', text: output }],
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      content: [{ type: 'text', text: `Bitrix24 error: ${message}` }],
      isError: true,
    };
  }
});

// ─── Start ────────────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
process.stderr.write('Bitrix24 BD Lead MCP server running.\n');
