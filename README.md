# bitrix24-bd-lead

An MCP (Model Context Protocol) server that automates B2B lead creation in Bitrix24 CRM. Given a qualified lead, it creates a Contact, a Deal, and 3 scheduled follow-up tasks (at +4, +9, and +14 days).

Designed to be used as a tool inside Claude via the MCP protocol.

---

## Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- A Bitrix24 account with admin access
- npm (comes with Node.js)

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd bitrix24-bd-lead
```

### 2. Install dependencies

```bash
npm install
```

### 3. Create your Bitrix24 webhook

1. Log in to your Bitrix24 account
2. Go to **Applications → Webhooks** in the left menu
3. Click **Add inbound webhook**
4. Enable permissions for: **CRM** and **Tasks**
5. Copy the generated URL — it looks like:
   `https://yourcompany.bitrix24.com/rest/123/abc456xyz/`

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and paste your webhook URL:

```
BITRIX24_WEBHOOK_URL=https://yourcompany.bitrix24.com/rest/YOUR_USER_ID/YOUR_WEBHOOK_TOKEN/
```

### 5. Build the project

```bash
npm run build
```

---

## Running the server

```bash
npm start
```

The server communicates over stdio and is meant to be launched by an MCP client (e.g., Claude Desktop or Claude Code). It will exit with an error if `BITRIX24_WEBHOOK_URL` is missing or invalid.

---

## Connecting to Claude

Add the following to your MCP client config (e.g., `claude_desktop_config.json` or `.claude/settings.json`):

```json
{
  "mcpServers": {
    "bitrix24-bd-lead": {
      "command": "node",
      "args": ["/absolute/path/to/bitrix24-bd-lead/build/index.js"],
      "env": {
        "BITRIX24_WEBHOOK_URL": "https://yourcompany.bitrix24.com/rest/YOUR_USER_ID/YOUR_WEBHOOK_TOKEN/"
      }
    }
  }
}
```

Restart Claude after saving the config.

---

## Development

Watch mode (auto-recompiles on file changes):

```bash
npm run dev
```

---

## Available scripts

| Script | Description |
|--------|-------------|
| `npm run build` | Compile TypeScript to `./build/` |
| `npm start` | Run the compiled server |
| `npm run dev` | Watch mode — recompile on changes |

---

## Tool reference

**Tool name:** `bitrix24_create_bd_lead`

**Required inputs:**

| Field | Description |
|-------|-------------|
| `company_name` | Target company name |
| `deal_name` | Deal title (format: `[Company] — [Signal in 3 words]`) |
| `signal` | What triggered this lead (e.g., "Series B funding announced") |
| `signal_type` | One of: `new_leadership`, `funding`, `hiring_gap`, `outdated_site`, `new_launch`, `negative_reviews` |
| `contact_name` | Decision maker's full name |
| `contact_role` | Their job title |
| `pain_point` | The business problem to address |
| `email_subject` | Subject line for the outreach email |
| `notes` | Any additional context |

**What it creates in Bitrix24:**
- 1 Contact (the decision maker)
- 1 Deal (linked to the contact)
- 3 follow-up tasks: Check + Connect (day +4), Short Bump (day +9), Close the Loop (day +14)
