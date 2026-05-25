# Market Research — CRM Alternatives

**Project:** `bitrix24-bd-lead` (MCP server that creates Contact + Deal + 3 follow-up Tasks for B2B outreach)
**Date:** 2026-05-22
**Author:** Bojan Bartoniček

---

## 1. Why look beyond Bitrix24

The current MCP server (`src/client.ts`) targets Bitrix24's REST webhook and calls three endpoints:

| Capability used | Bitrix24 endpoint |
|---|---|
| Create contact | `crm.contact.add` |
| Create deal linked to contact | `crm.deal.add` (with `CONTACT_ID`) |
| Create follow-up task linked to deal | `tasks.task.add` (with `UF_CRM_TASK = ["D_<dealId>"]`) |

**Friction with Bitrix24 today (refreshed 2026-05-22):**

1. **Free plan caps tasks at 100 total** (across all statuses: open, done, deferred). Users are unlimited and CRM + Tasks linking *is* available on free, but the 100-task ceiling means our MCP — which creates 3 follow-up tasks per lead — exhausts the free plan at ~33 leads. Sales-automation robots/workflows and multi-pipeline are paid-only. (Source: Bitrix24 helpdesk, "Limits in tasks on the free plan".)
2. **Heavy product.** Bitrix24 is a full-suite intranet (chat, drive, telephony, sites). Most BD/sales-only buyers find this overwhelming.
3. **REST quirks.** Webhook permissions per user, inconsistent field casing (`UPPER_SNAKE`), and `UF_CRM_TASK` array convention raise the bar for porting.
4. **Not common in our target market.** Croatian / EU SMBs we approach more often run HubSpot, Pipedrive, or nothing.

So: the MCP tool's value (auto-create lead skeleton + 3 follow-ups) should be portable to other CRMs.

---

## 1a. Regional Market Context — Central Europe & Africa

Our two target regions have very different CRM landscapes. This shapes which adapters we ship first.

### Central Europe / CIS

- **Bitrix24 is the regional default.** ~**19.12% global CRM market share** in the dataset surveyed, nearly 2× its closest non-enterprise competitor. ~**22,000–23,000 active domains** as of early 2025, with the steepest adoption curve running 2015–2022. Heavy concentration in Russian-speaking and CEE markets (confirmed by high Yandex.Metrika co-installation rates). (Source: technologychecker.io/technology/bitrix24, 2026.)
- **HubSpot is the upgrade path.** Migration data shows HubSpot gained net customers from Bitrix24 (114 in, 87 out) — buyers outgrowing Bitrix24's all-in-one bundle move to HubSpot or Salesforce.
- **Implication for us:** Shipping Bitrix24 first gives us the fastest path to a paying CEE customer (integration already done + buyers already there). HubSpot adapter then captures the upgrade migration.

### Africa (South Africa benchmark — best-documented African CRM market)

- **CRM share (South Africa, 2026):** Zendesk **20.7%**, ActiveCampaign **14.7%**, HubSpot **13%**, Zoho **5.4%**. (Source: maximizer.com Best CRM Software in South Africa 2026.)
- **MEA region:** Latin America + Middle East & Africa together projected at **~$18B CRM market value by 2030** — fast-growing, under-served. (Source: resonatehq.com HubSpot Market Share 2026.)
- **Local support footprint:** Only **HubSpot, Salesforce, and Microsoft Dynamics** have South Africa–based local support. Zoho, Pipedrive, Monday — international-only support. This is a real friction point for African SMB buyers and a tailwind for HubSpot in the region.
- **HubSpot global growth:** ~**20–25%/yr**, among the fastest of any major CRM vendor; strongest in SMB and mid-market (10–2,000 employees).
- **Implication for us:** HubSpot is the right second adapter for the Africa wedge. Zoho is worth a Phase 2 look given its price-sensitive-SMB positioning, even at low share.

### Regional pick summary

| Region | Dominant CRM | Our v1 adapter | Why |
|---|---|---|---|
| Central Europe / CIS | Bitrix24 (~19% global, ~22k domains) | **Bitrix24** | Already integrated, dominant locally, free-tier wedge via 100-task cap |
| Africa (SA + MEA) | Fragmented; HubSpot growing fastest with local support | **HubSpot** | 13% SA share, only major CRM with local SA support, 20–25% YoY growth |

---

## 2. CRM Alternatives Evaluated

Scoring axes (1–5):
- **Free tier viability** — can our MCP run end-to-end on the free plan?
- **API quality** — REST/JSON, auth simplicity, docs, rate limits
- **Object model fit** — Contact + Deal/Opportunity + Task with native linking
- **Market presence** — likelihood our outreach targets already use it
- **Effort to port** — relative dev time to swap `Bitrix24Client`

### Summary table

| CRM | Free tier viability | API | Object fit | Market | Port effort | Overall |
|---|---|---|---|---|---|---|
| **HubSpot CRM** | 4 (1k contacts / 2 users cap since Sept 2024) | 5 | 5 | 5 | Low | **Top pick** |
| **Pipedrive** (Lite €14/u/mo) | 2 (14-day trial only; no free tier) | 5 | 5 | 4 | Low | Strong (paid) |
| **Zoho CRM** | 4 (3 users) | 4 | 5 | 3 | Medium | Solid |
| **Attio** | 3 (3 users / 3 objects — tight for our pattern) | 4 | 3 | 2 (rising) | Medium | Modern bet |
| **Folk CRM** | 3 | 3 | 3 | 2 | Medium | Niche |
| **EspoCRM (self-host)** | 5 (OSS) | 4 | 5 | 1 | High | Sovereignty play |
| **SuiteCRM (self-host)** | 5 (OSS) | 3 | 5 | 1 | High | Heavy |
| **Monday CRM** | 2 | 4 | 4 | 3 | Medium | Skip |
| **Salesforce Starter** (~$25/u/mo) | 1 (no free) | 5 | 5 | 5 | High | Skip for free use |

### Detail

#### 1. HubSpot CRM — recommended primary target

- **Free tier (2026 reality check):** Free indefinitely, but **HubSpot tightened the free plan in Sept 2024**: new accounts are capped at **1,000 contacts** (down from 1M; older accounts grandfathered), **2 users**, **1 deal pipeline**, and **10 custom properties**. Tasks are included on free but no workflow automation. (Sources: claritysoft.com, engagebay.com, mo.agency — all dated 2026 updates.)
- **API:** Modern REST, OAuth2 + private app access tokens, JSON throughout. Excellent docs. Rate limit for marketplace OAuth apps: **110 requests per 10 seconds** per HubSpot account. (Source: developers.hubspot.com usage guidelines.)
- **Mapping our model:**
  - Our `Contact` → HubSpot `contacts` (`POST /crm/v3/objects/contacts`)
  - Our `Deal` → HubSpot `deals` (`POST /crm/v3/objects/deals`), associate to contact via `associations` array
  - Our `Task` → HubSpot `tasks` engagement (`POST /crm/v3/objects/tasks`), associated to deal + contact
- **Gotcha:** Task `hs_timestamp` is the *due date*, ms since epoch UTC — convert our `+4d / +9d / +14d` deadlines accordingly.
- **Why pick it:** Still the largest install base among the SMBs we prospect, free tier survives our use case (3 tasks × ~330 leads before hitting the 1,000-contact ceiling), cleanest API. **Caveat:** the 1,000-contact cap means heavy outbound users will graduate to paid Starter (~$15/seat/mo) faster than they used to — worth raising in the sales pitch.

#### 2. Pipedrive — strong if buyer already paying

- **Free tier:** None — 14-day trial only.
- **Plan rename (July 2025):** Pipedrive rebranded tiers — **Essential → Lite ($14)**, Advanced → Growth ($39), Professional/Power → Premium ($49), Enterprise → Ultimate ($79), all per user/month annual. (Sources: pipedrive.com/pricing, axisconsulting.io 2026 guide.)
- **API:** Token-based, very simple. Available on **all plans including Lite**. Rate limits: **80 req / 2s on Lite**, up to 200 req/2s on Ultimate. `POST /v1/persons`, `POST /v1/deals`, `POST /v1/activities` (activities are Pipedrive's "tasks"; `type: "call"|"email"|"task"`).
- **Object fit:** Excellent — Pipedrive is explicitly sales-pipeline-first. Activities have a `due_date` field, native.
- **Why consider:** If a prospect is already on Pipedrive, port is trivial — the data model is closer to ours than HubSpot's. Note: v1 API is being progressively deprecated in favour of v2 for some endpoints; verify endpoint version before locking in.

#### 3. Zoho CRM — best free tier outside HubSpot

- **Free tier:** Up to 3 users, includes Leads, Contacts, Deals, Tasks, basic workflow.
- **API:** REST + OAuth2. Slightly more ceremony (refresh-token dance, regional data-center routing — `.com` vs `.eu`).
- **Object fit:** Native `Leads` + `Contacts` + `Deals` + `Tasks`. Tasks have `Due_Date` and `What_Id` to link to a Deal.
- **Why consider:** Free, EU data-center option (good for GDPR pitches), strong in Indian/EU SMB market.

#### 4. Attio — modern, AI-native

- **Free tier (2026):** Up to **3 users**, **50,000 records**, **3 objects total** (People + Companies + 1 additional standard or custom), 200–250 emails/mo. (Sources: attio.com/pricing, stacksync.com 2026 review.)
- **API:** REST (no public GraphQL despite earlier marketing). Auth via API key or OAuth. Schema is user-defined — workspace must have `companies`, `people`, plus a `deals` and tasks-equivalent object configured before our MCP can write. API access is on **all plans including free**, though Attio reserves the right to throttle without notice; community reports suggest ~1,000 calls/hour as a practical ceiling.
- **Object fit:** Customisable; strong for modern startups but the 3-object cap on free means a workspace can fit Companies + People + Deals — leaving **no room for a separate Tasks object on free**. Tasks would need to be modelled as notes or a custom field, or the buyer upgrades.
- **Why consider:** Hot product, well-funded, attractive to tech-forward prospects. Riskier as a default because schema isn't fixed and the free-tier object cap squeezes our 3-task pattern.

#### 5. EspoCRM / SuiteCRM (self-hosted, open-source)

- **Free tier:** Free (open source). Self-host on a VPS — €5/mo droplet works.
- **API:** EspoCRM has a clean REST API with API key auth. SuiteCRM v8 has REST v8 (OAuth2); v7 had SOAP/legacy REST.
- **Object fit:** Native Account/Contact/Opportunity/Task — closest to enterprise Salesforce model.
- **Why consider:** Data-sovereignty pitch for EU/regulated buyers (HACCP / pharma / finance). Higher port + hosting effort.

---


## References

Primary API docs:
- HubSpot CRM API: https://developers.hubspot.com/docs/api/crm
- HubSpot API usage guidelines (rate limits): https://developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines
- Pipedrive API (v1 + v2): https://developers.pipedrive.com/docs/api/v1
- Zoho CRM API: https://www.zoho.com/crm/developer/docs/api/
- Attio API: https://developers.attio.com/
- EspoCRM API: https://docs.espocrm.com/development/api/
- Bitrix24 task limits on free plan: https://helpdesk.bitrix24.com/open/18219254/

2026 pricing & free-tier verification (retrieved 2026-05-22):
- HubSpot 2026 free-plan limits (1k contacts, 2 users, Sept 2024 change): https://claritysoft.com/hubspot-free-plan-limitations/, https://www.engagebay.com/blog/is-hubspot-free/
- Pipedrive 2026 plans + July 2025 rename: https://www.pipedrive.com/en/pricing, https://axisconsulting.io/pipedrive-pricing-plans/
- Attio 2026 free-plan caps (3 users / 50k records / 3 objects): https://attio.com/pricing/eur, https://www.stacksync.com/blog/attio-crm-2025-review-features-pros-cons-pricing
- Bitrix24 2026 free plan overview: https://www.bitrix24.com/prices/

Regional market data (retrieved 2026-05-25):
- Bitrix24 global share & domain footprint: https://technologychecker.io/technology/bitrix24
- HubSpot 2026 market share & growth: https://www.resonatehq.com/blog/hubspot-market-share
- Best CRM Software in South Africa 2026 (regional share, local support): https://www.maximizer.com/blog/best-crm-software-south-africa/
- Top CRM Statistics 2026: https://www.sellerscommerce.com/blog/crm-statistics/

## Changelog

- **2026-05-22** — Refreshed free-tier and pricing data for HubSpot (Sept 2024 contact cap), Pipedrive (July 2025 plan rename), Attio (3-object free-plan ceiling), and Bitrix24 (100-task free cap clarified). Earlier version inaccurately stated Bitrix24 tasks required a paid plan; the gate is the 100-task ceiling, not the feature itself.
- **2026-05-25** — Added §1a Regional Market Context covering Central Europe/CIS and Africa: Bitrix24 ~19% global share + ~22k active domains concentrated in CEE/CIS; SA CRM breakdown (HubSpot 13%, Zoho 5.4%, Zendesk 20.7%); $18B MEA market projection by 2030. Regional adapter picks tied explicitly to these numbers — Bitrix24 for CEE wedge, HubSpot for Africa.
