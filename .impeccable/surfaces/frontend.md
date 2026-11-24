---
version: 1
slug: "frontend"
primary_target: "frontend"
related_targets: []
---

# Surface: EventZilla analysis app (frontend/)

Scope: the whole Angular app. Visitor mode: **Operate** (managers answer one business question at a time and decide).
Audience and job: EventZilla managers, non-technical; read before or during a meeting, laptop first, phone must hold.
Content: the four business objectives (revenue, reservations, customers, marketing), data quality, the analyst assistant. All figures from /api on the live warehouse; synthetic-data note on every page.
Locked structure: "The market board" (surface seed d890e22b, dealt candidate 1 of 7).

## Direction contract

THESIS: The business read as a board of markets. Each objective is a market tile that states its figure, its change and its trend; opening it gives the full chart and the ranked outcomes behind it. Refuses the category default of a sidebar, a row of KPI cards and a grid of unrelated charts.

OWN-WORLD: "Trading desk", chosen by the owner on 2026-11-24 as the business palette: navy ground #0b1220, plates #111a2e with 1 px line #1f2a44, recessed chart panels #0a1020, ink #e6ebf5 / #9aa8c3, one electric-blue data line #3b82f6 with a faint area under it, green #22c55e and red #ef4444 only for up and down, orange #f97316 only for the gate (quality rule that excluded rows, model that failed its gate). Manrope for words, JetBrains Mono for figures and readouts (tabular). The owner's identity survives as influence only: one gate signal, instrument readouts. Outcome rows as thin bars with share and value, like a market's outcome list.

STORY: The manager sees in one screen how each objective is doing and how far to trust it, opens the one that matters, sees what drives it, and asks the assistant the next question, or types /questions to get the questions worth asking with their current value and the decision each informs.

FIRST VIEWPORT: Top bar: wordmark, page keys (Board, Revenue, Reservations, Customers, Marketing, Quality), synthetic-data note. Left 8 columns: 2 × 2 market tiles, each a recessed display with label, headline readout (clamp 1.75-2.75rem mono), change vs last year, 48-month sparkline with crosshair; a data-quality strip under them (rows excluded, gate status). Right 4 columns: the analyst assistant docked, full height, input at the bottom, Ask is the one solid blue key.

FORM: Market board, my ranked list position 1 (of 7), seed key d890e22b. Signature interaction: the assistant's answer arrives as a staged readout (screened → query written → guarded → rows → answer) with GSAP, then its chart draws in on the display; crosshair readouts on every chart.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
