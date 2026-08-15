/* ============================================================
   bd-lead — sample data + inline icon set (shared to window)
   Lead Brief structure matched to the artifact:
   Snapshot · Buying Signal · Contact (confidence) · Email · CRM + 3 follow-ups.
   ============================================================ */

const LEAD = {
  name: "Lena Vuković",
  email: "lena.vukovic@maritimo-logistics.hr",
  linkedin: "linkedin.com/in/lenavukovic",
  // enriched
  title: "Head of Operations",
  company: "Maritimo Logistics",
  companyDomain: "maritimo-logistics.hr",
  location: "Rijeka, Croatia",
  industry: "Freight & shipping",
  headcount: "120–180",
  founded: "2009",

  // 3-sentence company snapshot
  snapshot:
    "Maritimo Logistics is a Rijeka-based freight forwarder moving containerised cargo across the Adriatic for retail and manufacturing shippers. Founded in 2009, it runs ~150 staff and is expanding into rail-linked inland routes after a 2026 terminal partnership. The company is privately held, profitable, and scaling dispatch volume faster than its current tooling supports.",

  // the single highest-priority buying signal
  signal: {
    source: "LinkedIn",
    date: "May 2026",
    priority: 1,
    text: "Maritimo is hiring 3 dispatch + customs coordinators in 30 days — a structural strain on follow-up between handoffs, and the ideal window to position a tighter quote-to-booking process while the team scales.",
  },

  // contact target + verification (HIGH / MEDIUM / LOW)
  contact: {
    confidence: "HIGH",
    sources: 2,
    note: "Lena Vuković, Head of Operations — confirmed on LinkedIn and the Maritimo site (/team). Under pressure to keep booking times flat while volume climbs ahead of peak season.",
  },

  // personalized outreach email (signal-matched, under 90 words)
  outreach: {
    subject: "While Maritimo scales dispatch",
    words: 71,
    angle: "Hiring strain → empathy",
    body:
      "Hi Lena — saw Maritimo just tied up the Rijeka–Zagreb rail link and is staffing up dispatch. Teams scaling that fast usually start dropping follow-ups between handoffs.\n\nWe've helped two Adriatic forwarders cut quote-to-booking time without adding headcount — keeping things moving while new coordinators ramp.\n\nWorth a 20-minute call Thursday or Friday?",
  },

  confidence: 0.86,
  sources: 7,
};

// supporting signals shown as a priority-ordered checklist
const SIGNALS = [
  { kind: "Hiring",  pri: 1, on: true,  text: "3 dispatch + customs roles posted in 30 days (LinkedIn)" },
  { kind: "News",    pri: 2, on: true,  text: "Rijeka–Zagreb rail terminal partnership, Mar 2026" },
  { kind: "Tech",    pri: 3, on: false, text: "Runs Bitrix24; site on Cloudflare + HubSpot forms" },
  { kind: "Reviews", pri: 4, on: false, text: "No recent review momentum — not the lead signal" },
];

const CADENCES = { "4/9/14": [4, 9, 14], "3/7/14": [3, 7, 14], "2/5/10": [2, 5, 10] };

function buildPlan(cadenceKey) {
  const days = CADENCES[cadenceKey] || CADENCES["4/9/14"];
  return [
    {
      day: days[0], type: "Email", title: "Send personalized opener",
      desc: "Reference the rail-link expansion + dispatch hiring. Attach the Adriatic forwarder case study.",
      script: "Open on the signal, one specific proof point, single CTA. If no open by +2: resend with alternate subject.",
    },
    {
      day: days[1], type: "Call", title: "Discovery call — quote-to-booking flow",
      desc: "Map where follow-ups slip between dispatch handoffs. Goal: book a 20-min ops walkthrough.",
      script: "\"Still scaling the dispatch team? We've bridged this exact gap for a couple of forwarders — worth 15 minutes?\"",
    },
    {
      day: days[2], type: "LinkedIn", title: "Share proof + soft close",
      desc: "Send the time-to-booking metric as a LinkedIn note. Propose a pilot scoped to one lane.",
      script: "\"Last note from me — if timing's off, no problem. If booking speed becomes a priority, you know where we are.\"",
    },
  ];
}

// per-user memory — the "gets smarter the more you use it" differentiator
const MEMORY = [
  { icon: "tone", text: "Matched your tone — short, warm, one clear ask. Learned from 23 emails you've sent." },
  { icon: "cadence", text: "Used your 4/9/14 cadence — your booked deals average a call by day 9." },
  { icon: "icp", text: "Maritimo fits your ICP: Croatian logistics, 100–250 staff. You've won 4 like it." },
];

const CRM = {
  bitrix24: { name: "Bitrix24", color: "var(--accent3)", short: "B24" },
  hubspot:  { name: "HubSpot",  color: "var(--gold)",   short: "HS" },
};

// ---- icons (24-grid, currentColor stroke) ----
const I = {
  spark: 'M12 2l1.6 5.3L19 9l-5.4 1.7L12 16l-1.6-5.3L5 9l5.4-1.7z',
  bolt: 'M13 2L4 14h7l-1 8 9-12h-7z',
  check: 'M20 6L9 17l-5-5',
  arrow: 'M5 12h14M13 6l6 6-6 6',
  plus: 'M12 5v14M5 12h14',
  mail: 'M3 6h18v12H3zM3 7l9 6 9-6',
  phone: 'M4 4h4l2 5-3 2a14 14 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 014 6a2 2 0 010-2z',
  link: 'M9 15l6-6M10 6l1-1a4 4 0 016 6l-1 1M14 18l-1 1a4 4 0 01-6-6l1-1',
  clock: 'M12 7v5l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  user: 'M20 21a8 8 0 10-16 0M12 11a4 4 0 100-8 4 4 0 000 8z',
  building: 'M3 21h18M5 21V5l7-2v18M19 21V9l-7-2M9 9h0M9 13h0M15 13h0M15 17h0',
  pin: 'M12 21s7-6 7-11a7 7 0 10-14 0c0 5 7 11 7 11zM12 12a2.5 2.5 0 100-5 2.5 2.5 0 000 5z',
  memory: 'M12 3a4 4 0 00-4 4 3 3 0 00-1 5.8V17a3 3 0 006 0V3zM12 3a4 4 0 014 4 3 3 0 011 5.8',
  shield: 'M12 3l7 3v6c0 4-3 7-7 8-4-1-7-4-7-8V6z',
  refresh: 'M3 12a9 9 0 0115-6.7L21 8M21 12a9 9 0 01-15 6.7L3 16M21 4v4h-4M3 20v-4h4',
  edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z',
  chevron: 'M9 6l6 6-6 6',
  chevronD: 'M6 9l6 6 6-6',
  x: 'M6 6l12 12M18 6L6 18',
  copy: 'M9 9h11v11H9zM5 15H4V4h11v1',
  doc: 'M14 3v5h5M7 3h8l5 5v13H7zM10 13h7M10 17h7',
  target: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 16a4 4 0 100-8 4 4 0 000 8zM12 12h0',
  layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5',
  card: 'M3 7h18v11H3zM3 10h18',
  zap: 'M13 2L4 14h7l-1 8 9-12h-7z',
  star: 'M12 3l2.5 5.6L20 9.3l-4 4 1 5.7L12 16.5 7 19l1-5.7-4-4 5.5-.7z',
  users: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8',
  lock: 'M5 11h14v10H5zM8 11V7a4 4 0 018 0v4',
  download: 'M12 3v12M7 10l5 5 5-5M5 21h14',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4z',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.6 1.6 0 00-2.7 1.1V21a2 2 0 01-4 0v-.1A1.6 1.6 0 005 19.4l-.1.1a2 2 0 11-2.8-2.8l.1-.1A1.6 1.6 0 003.3 14H3a2 2 0 010-4h.1A1.6 1.6 0 004.6 5L4.5 5a2 2 0 112.8-2.8l.1.1A1.6 1.6 0 0010 3.3V3a2 2 0 014 0v.1a1.6 1.6 0 002.7 1.1l.1-.1a2 2 0 112.8 2.8l-.1.1a1.6 1.6 0 00-.3 1.8',
};

function Icon({ d, size = 16, sw = 1.7, style }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round"
      style={{ flexShrink: 0, ...style }}>
      {(Array.isArray(I[d]) ? I[d] : (I[d] || d).split("|")).map((p, i) => <path key={i} d={p} />)}
    </svg>
  );
}

const typeIcon = { Email: "mail", Call: "phone", LinkedIn: "link" };

Object.assign(window, { LEAD, SIGNALS, CADENCES, buildPlan, MEMORY, CRM, I, Icon, typeIcon });
