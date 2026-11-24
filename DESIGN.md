---
name: EventZilla analytics
description: The business read as a board of markets, with an analyst that shows its work.
colors:
  navy-ground: "#0b1220"
  plate: "#111a2e"
  plate-hover: "#15203a"
  display-well: "#0a1020"
  line: "#1f2a44"
  line-strong: "#2c3a5c"
  ink: "#e6ebf5"
  ink-2: "#b4c0d6"
  ink-3: "#8a98b5"
  data: "#3b82f6"
  data-deep: "#2f74e6"
  data-ink: "#7fb0ff"
  data-fill: "rgb(59 130 246 / 0.1)"
  series-2: "#94a3b8"
  up: "#22c55e"
  down: "#f87171"
  gate: "#f97316"
  gate-fill: "rgb(249 115 22 / 0.1)"
  on-data: "#ffffff"
typography:
  readout:
    fontFamily: "JetBrains Mono Variable, ui-monospace, monospace"
    fontSize: "clamp(1.75rem, 3.2vw, 2.5rem)"
    fontWeight: 560
    lineHeight: 1
    letterSpacing: "-0.035em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Manrope Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 2.4vw, 1.875rem)"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Manrope Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title-sm:
    fontFamily: "Manrope Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Manrope Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "ss01"
  body-sm:
    fontFamily: "Manrope Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
  figure:
    fontFamily: "JetBrains Mono Variable, ui-monospace, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    fontFeature: "tnum"
  label:
    fontFamily: "JetBrains Mono Variable, ui-monospace, monospace"
    fontSize: "0.6875rem"
    fontWeight: 400
    letterSpacing: "0.04em"
rounded:
  control: "6px"
  popover: "8px"
  display: "10px"
  plate: "12px"
spacing:
  tight: "0.375rem"
  row: "0.875rem"
  tile: "1rem"
  section: "1.25rem"
  panel: "1.125rem 1.25rem 1.25rem"
  page: "clamp(1rem, 2.2vw, 1.75rem)"
components:
  key:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.control}"
    padding: "0 0.75rem"
    height: "32px"
  key-hover:
    backgroundColor: "{colors.plate-hover}"
    textColor: "{colors.ink}"
  key-on:
    backgroundColor: "{colors.plate-hover}"
    textColor: "{colors.ink}"
  key-primary:
    backgroundColor: "{colors.data}"
    textColor: "{colors.on-data}"
    rounded: "{rounded.control}"
    padding: "0 0.75rem"
    height: "32px"
  key-primary-hover:
    backgroundColor: "{colors.data-deep}"
  plate:
    backgroundColor: "{colors.plate}"
    rounded: "{rounded.plate}"
    padding: "{spacing.panel}"
  chart-well:
    backgroundColor: "{colors.display-well}"
    rounded: "{rounded.display}"
    padding: "0.875rem 0.875rem 0.5rem"
  segmented:
    backgroundColor: "{colors.display-well}"
    textColor: "{colors.ink-3}"
    rounded: "{rounded.popover}"
    height: "36px"
  segmented-on:
    backgroundColor: "{colors.line-strong}"
    textColor: "{colors.ink}"
  composer-input:
    backgroundColor: "{colors.display-well}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.75rem"
    height: "40px"
  nav-link:
    textColor: "{colors.ink-3}"
    padding: "0 0.75rem"
    height: "60px"
  nav-link-active:
    textColor: "{colors.ink}"
  change-good:
    textColor: "{colors.up}"
    typography: "{typography.figure}"
  change-bad:
    textColor: "{colors.down}"
    typography: "{typography.figure}"
  gate-note:
    backgroundColor: "{colors.gate-fill}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.display}"
    padding: "0.75rem 0.875rem"
  trust-popover:
    backgroundColor: "{colors.plate-hover}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.popover}"
    padding: "0.75rem 0.875rem"
    width: "min(20rem, calc(100vw - 2rem))"
  starter:
    backgroundColor: "{colors.display-well}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0.625rem 0.75rem"
---

# Design System: EventZilla analytics

## Overview

**Creative North Star: "The Trading Desk"**

The business is read as a board of markets. Each objective (revenue, reservations, customers, marketing) is a market tile that states its figure, its change and its trend; opening it gives the full chart and the ranked outcomes behind it. The owner locked the palette and type on 2026-11-24: navy grounds, Manrope for words, JetBrains Mono for figures only. The world is a dark instrument panel, calm and dense: plates sit on the navy ground, charts sit in recessed wells, and one electric-blue line carries the data.

Colour is evidence, not decoration. Blue means "this is the data"; green and red mean "this change is good or bad news"; orange means "the gate stopped something". Nothing else gets a hue. Statistics (p-values, correlations, model names, the query) are kept out of the default reading and live behind the info popovers and the analyst's "Show the work". Headline figures always render settled, never counted up; motion is spent on one thing, the analyst's staged replay of how it reached an answer.

The app refuses the category default of a sidebar, a row of KPI cards and a grid of unrelated charts. Navigation is a top bar of page keys; the analyst is docked on the right at full height on wide screens.

**Key Characteristics:**
- Navy ground, flat plates with 1px lines, recessed chart wells: depth by tone, not shadow.
- One electric-blue data line with a faint area under it; second series in slate, dashed when it is a projection.
- Green and red only on changes, coloured by news, not by direction; the arrow gives the direction.
- Orange reserved for the gate: rows a quality rule kept out, a model or question stopped.
- Manrope for words, JetBrains Mono (tabular) for figures and nothing else.
- Market anatomy repeated on every objective page: figure, change, chart well, ranked outcome rows.
- Statistics behind popovers and "Show the work"; the default reading stays in plain language.

## Colors

A near-monochrome navy desk with one blue data voice and three signal colours that each have exactly one job.

### Primary
- **Electric Data Blue** (`data`): the data line on every chart, the end-of-line dot, the active nav underline, the selected-key border, focus rings, the caret, and the one solid key (Ask). Its area fill is `data-fill`, drawn at about 9% opacity under the main series only.
- **Pressed Data Blue** (`data-deep`): the hover state of the solid blue key. Used nowhere else.
- **Data Ink** (`data-ink`): blue as text on dark grounds: links, "today's answer" values in question lists, slash-command names, the query in "Show the work", hovered tile titles and arrows.

### Secondary
- **Slate Series** (`series-2`): every non-primary series and every non-leading outcome bar: the forecast (dashed), pending and cancelled reservations, marketing spend. It keeps comparison visible without competing with the blue line.

### Tertiary (signals)
- **Good-News Green** (`up`): a change that is good news, whichever way it moves.
- **Bad-News Red** (`down`): a change that is bad news; lightened from red-500 so text meets AA on the plates. Also the colour of the "service did not answer" error line.
- **Gate Orange** (`gate`, `gate-fill`): the count of rows a rule left out, a failed gate, the analyst's stopped step, the gate note. `gate-fill` is its 10% wash, with a 40% orange border.

### Neutral
- **Navy Ground** (`navy-ground`): the page and the translucent top bar (at 92% with a 10px blur). Also the browser theme colour.
- **Plate** (`plate`): the one container surface: tiles, panels, the analyst dock, the palette box.
- **Plate Hover** (`plate-hover`): hovered keys and rows, the pressed key, popovers and menus.
- **Display Well** (`display-well`): the recessed surface, darker than the ground: chart wells, segmented tracks, inputs, the analyst's step list, starters and question buttons, bar tracks.
- **Line** (`line`) and **Strong Line** (`line-strong`): 1px plate borders and row dividers; key borders, hover borders, scrollbar thumbs, the segmented thumb.
- **Ink** (`ink`), **Ink 2** (`ink-2`), **Ink 3** (`ink-3`): headings and figures; body sentences and secondary keys; labels, axis ticks, captions, the crosshair.

### Named Rules
**The One Line Rule.** One electric-blue data line per chart. Every other series is slate; a projection is slate and dashed. In ranked outcomes only the leading row is blue.

**The News Not Direction Rule.** Green is good news and red is bad news, on changes only. A cost that falls is green; the arrow, not the colour, says which way it moved. A change under its "small" threshold says "small" in words and is never dramatised.

**The Gate Owns Orange Rule.** Orange appears only where the gate acted: rows kept out of a figure, a model that failed its check, a question the analyst stopped. No orange for emphasis, warnings in general, or decoration.

The build also paints *passed* checks green (the "Passed the gate" line on the board, the pass-note icon, the analyst's ticked steps). That extends the locked "changes only" rule and is recorded here as built, pending the owner's confirmation.

## Typography

**Display Font:** none; there is no display face.
**Body Font:** Manrope Variable (with ui-sans-serif, system-ui, sans-serif), stylistic set `ss01` on.
**Label/Mono Font:** JetBrains Mono Variable (with ui-monospace, monospace), tabular numerals, slashed zero off.

**Character:** A quiet geometric sans for every sentence and an instrument mono for every figure, so a number is recognisable as a reading at a glance.

### Hierarchy
- **Readout** (JetBrains Mono 560, `clamp(1.75rem, 3.2vw, 2.5rem)`, line-height 1, -0.035em): the headline figure of an objective page and the analyst's single-number answers. On board tiles it is reduced to `clamp(1.75rem, 2.4vw, 2.25rem)`. Units sit beside it in Ink 3 mono at 0.875rem.
- **Headline** (Manrope 650, `clamp(1.5rem, 2.4vw, 1.875rem)`, 1.15, -0.02em, balanced): one per page, the page's business question as a title.
- **Title** (Manrope 650, 1.0625rem, 1.3): section and tile headings (tiles use 1.125rem). Small title at 0.9375rem for analyst answer titles and h3.
- **Body** (Manrope 400, 0.9375rem, 1.55): sentences; page leads capped at 64ch, trust notes at 72ch.
- **Body small** (Manrope, 0.8125rem): keys, figure labels, captions, trust notes, step lists.
- **Figure** (JetBrains Mono, tabular): every number in prose position: changes (0.8125rem), facts (1.0625rem, 560), outcome values (0.875rem), axis ticks (10.5px), table cells.
- **Label** (JetBrains Mono, 0.6875rem, 0.04em, uppercase, Ink 3): instrument labels only: the "analytics" mark beside the wordmark, the popover's "How this is computed", fact labels, the analyst's single-figure label.

### Named Rules
**The Mono Means Measured Rule.** JetBrains Mono is for figures alone: values, units, periods, axis ticks, commands, the query. Words, questions and explanations are always Manrope.

**The Settled Headline Rule.** A headline figure is rendered at its final value. Nothing counts up; a manager reading over a shoulder must never catch a false number.

## Layout

The desk is a two-column grid: the page (`minmax(0, 1fr)`) and the docked analyst (`clamp(22rem, 30vw, 27rem)`), under a sticky 60px top bar. The analyst is sticky at full remaining height with its input at the bottom.

Pages are a single grid column with `clamp(1rem, 2.2vw, 1.75rem)` padding and 1.25rem gaps (the board tightens to 1rem). The board is 2 x 2 market tiles, each laid out "figure left, trend right" (`1.1fr / 1fr`), with the data-quality strip ("Before these figures") spanning beneath. Objective pages repeat one anatomy, the market panel: figure and change top-left, controls top-right, a full-width chart well, then a pass or gate note; then ranked outcome panels; then "Questions to decide on". Two-up panels use `auto-fit, minmax(min(100%, 22rem), 1fr)`.

Responsive steps (all observed): at 87.5rem the year range leaves the synthetic-data note; at 80rem the quality strip stacks; at 68.75rem the analyst leaves the grid and becomes a right drawer (`min(28rem, 100vw)`) opened by an "Ask" key; at 56rem the board goes to one column; at 47.5rem the bar becomes two rows (96px, page keys scroll horizontally with a fade) and the drawer goes full width; at 40rem a tile stacks figure over chart; at 30rem an outcome row puts its bar on its own line.

Spacing rhythm is small and steady: 0.375rem between keys, 0.875rem between a section head and its content and between outcome columns, 1-1.25rem between plates.

## Elevation & Depth

Flat by default. Depth comes from tone: the navy ground, the slightly lighter plate on top of it, and the display well that is *darker* than the ground, so charts read as recessed instrument screens. Plates carry a 1px line and no shadow. Shadows exist only on things that float over the page.

### Shadow Vocabulary
- **Drawer** (`box-shadow: -24px 0 48px rgb(0 0 0 / 0.4)`): the analyst when it slides in as a drawer below 68.75rem.
- **Popover** (`box-shadow: 0 16px 40px rgb(0 0 0 / 0.5)`): the "How this is computed" popover.
- **Menu** (`box-shadow: 0 12px 32px rgb(0 0 0 / 0.45)`): the slash-command menu above the composer.
- **Palette** (`box-shadow: 0 24px 64px rgb(0 0 0 / 0.55)`): the Ctrl/Cmd K palette, over a `rgb(5 9 18 / 0.6)` backdrop with a 3px blur.

### Named Rules
**The Recessed Display Rule.** Charts never sit directly on a plate: they sit in a display well (darker than the ground, 1px line, 10px corners), the way a reading sits in a screen.

**The Floating-Only Shadow Rule.** A shadow means the element floats above the page (drawer, popover, menu, palette). Plates and tiles never get one; hover raises a border to Strong Line instead.

## Shapes

Gently rounded, nested by size: controls 6px, popovers and segmented tracks 8px, display wells 10px, plates 12px, so an inner corner is always tighter than its container. Lines are always 1px; the only 2px strokes are the data line, the active-nav underline and focus rings. Outcome bars are 6px tall with 3px ends. Status marks in the analyst's step list are 16px circles. Icons are authored on a 24-unit grid, 1.75 stroke, round caps and joins, one family for the whole app.

## Components

### Keys (buttons)
Quiet outlined keys; only one key is ever solid.
- **Shape:** gently rounded (6px), 32px tall (40px in the composer), 0.75rem side padding, Manrope 600 at 0.8125rem.
- **Default:** transparent with a Strong Line border and Ink 2 text.
- **Hover / Pressed:** Plate Hover background, Ink text; a pressed or "on" key also takes a blue border. Active presses down 1px. Transitions 140ms on the house ease.
- **Primary:** solid Data Blue with white text, used for Ask only (in the composer and the narrow-screen bar); hover darkens to Pressed Data Blue.
- **Disabled:** 45% opacity.

### Segmented control
A display-well track (8px) with a Strong Line thumb that slides to the chosen segment (transform only, 260ms). Segments are 28px, Manrope 600, Ink 3, the chosen one Ink. It is a radio group: arrow keys move the choice.

### Plates and chart wells
- **Plate:** the one container. Plate background, 1px Line border, 12px corners, no shadow; hovered tiles raise the border to Strong Line.
- **Chart well:** Display Well, 1px Line, 10px corners, holding a line chart.

### Line chart (signature data form)
Market-style: values on the right axis, mono ticks in Ink 3, 1px Line gridlines, value axis from zero unless a domain is given (a cropped axis would turn synthetic noise into drama). A dotted Ink 3 crosshair scrubs every series at once and the legend shows the reading; it is keyboard-scrubbable (arrows, Home, End) and carries a hidden data table. The latest point carries a filled dot. Board tiles use a compact 118px version with a "peek" reading in the corner instead of a legend.

### Ranked outcomes
A market's outcome list: name (with an optional subline), a 6px bar in a display-well track scaled against the largest row, the figure right-aligned in mono. The leading row is blue, the rest slate; rows a rule left out are orange. Rows are separated by 1px lines.

### Change chip
A 12px arrow plus a signed mono figure, coloured by news (good green, bad red, flat Ink 3), followed by its reference period in Ink 3 and the word "small" when under its threshold.

### Trust popover
Every headline figure carries a 22px round info button. It opens a native popover (Plate Hover, Strong Line, 8px, max 20rem) headed "How this is computed", with the definition, period and the rules that touched the figure. It fades and rises 4px in 160ms.

### Gate and pass notes
- **Gate note:** orange 10% wash, 40% orange border, 10px corners, orange stop-shield icon, Ink 2 text with an Ink lead. Appears only where the gate acted.
- **Pass note:** display-well background, Line border, green shield icon: a check that passed, stated plainly.

### Navigation
Top bar, 60px, translucent navy with a 10px blur and a bottom Line. Page keys are Manrope 560 at 0.875rem in Ink 3, Ink on hover and when current; the current page gets a 2px blue underline that slides between pages as a view transition (300ms). A synthetic-data note in mono with its own trust popover and a "Go to or ask" key (Ctrl/Cmd K) sit at the right.

### Analyst (signature component)
The docked assistant: a plate column with a head, a scrolling log and a composer. Starters and "/questions" items are display-well buttons; a question shows its text (Manrope 600), today's answer in Data Ink and "Decides:" in Ink 3. Each answer begins with its step list in a display well: green ticked marks for steps done, an orange stop mark and orange text for a step the gate stopped. The answer text, then a chart, number or table in a display well, then a collapsed **Show the work** with the query in Data Ink mono and the row count. Waiting shows a 56px scan bar with a blue sweep.

**The signature moment** is the staged replay: when an answer arrives, its route plays once (GSAP, expo.out): the steps (checked, written, approved, rows) slide in 0.09s apart with their marks scaling in, the answer wipes in left to right (clip-path, 0.7s), then the result rises out of a 4px blur and its line chart traces in. A stopped question lands its orange mark with a back-out overshoot instead. Reduced motion removes all of it.

### Command palette
Ctrl/Cmd K opens a modal dialog: a 52px search field, then grouped results (pages, questions worth asking with today's answer, "Ask the analyst"). The active row takes Plate Hover with a 2px inset blue edge. It drops in 6px in 0.18s.

### Motion
One ease for everything: `cubic-bezier(0.16, 1, 0.3, 1)`. Colour and border changes 140ms, small transforms 160ms. Pages cross-fade (out 140ms, in 320ms with a 6px rise and 2px blur). Lines trace in (0.9s, staggered 0.08s) only where the chart is asked to animate: the board tiles and the analyst's results. Headline figures never animate. `prefers-reduced-motion` collapses every animation and transition.

## Do's and Don'ts

### Do:
- **Do** draw exactly one series in Data Blue per chart, with its faint area; use Slate Series for every comparison and dash it when it is a projection.
- **Do** colour a change by whether it is good news (`good="down"` for costs) and let the arrow carry the direction; say "small" in words below the threshold.
- **Do** reserve orange for the gate: rows left out, a failed check, a stopped question.
- **Do** set every figure in JetBrains Mono with tabular numerals and every word in Manrope.
- **Do** put charts in a recessed display well (Display Well, 1px Line, 10px corners) inside a 12px plate.
- **Do** attach a "How this is computed" popover to every headline figure, and keep p-values, correlations, model names and the query behind popovers or "Show the work".
- **Do** render headline readouts settled at their final value.
- **Do** keep the synthetic-data note visible and quiet on every page.

### Don't:
- **Don't** introduce any hue beyond navy neutrals, Data Blue, Slate, the green/red change pair and Gate Orange.
- **Don't** use green or red to mean "up" or "down"; a falling cost is green.
- **Don't** use orange for emphasis, generic warnings or decoration.
- **Don't** count up, tick, or animate a headline figure; draw-in belongs to the board's first load and the analyst's results only.
- **Don't** put shadows on plates or tiles; shadows are for floating layers only.
- **Don't** crop a value axis to make flat synthetic data look dramatic.
- **Don't** show a currency symbol; the source documents none.
- **Don't** put technical words (fact, dimension, SQL) in the default reading; they belong in "Show the work".
