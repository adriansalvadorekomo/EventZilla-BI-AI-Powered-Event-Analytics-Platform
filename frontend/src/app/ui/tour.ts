import { ChangeDetectionStrategy, Component, ElementRef, OnInit, computed, effect, inject, output, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { AssistantStore } from '../assistant/store';
import { Icon } from './icon';

type Action =
  | { kind: 'go'; label: string; to: string }
  | { kind: 'ask'; label: string; text: string }
  | { kind: 'palette'; label: string }
  | { kind: 'link'; label: string; href: string };

interface Step {
  title: string;
  body: string[];
  /** CSS selector of the part of the page this step explains (outlined while the step is open) */
  spot?: string;
  /** the page this step is about; the tour navigates there */
  route?: string;
  /** which side the card sits on, so it never covers what it explains */
  side?: 'left' | 'right';
  actions?: Action[];
}

const REPO = 'https://github.com/adriansalvadorekomo/EventZilla-BI-AI-Powered-Event-Analytics-Platform';
const PORTFOLIO = 'https://adriansalvadorekomodev.vercel.app';

const STEPS: Step[] = [
  {
    title: 'A 60-second tour',
    side: 'left',
    body: [
      'EventZilla is the analytics platform of an event-services marketplace. I rebuilt it alone: the data lands in a warehouse, is tested and gated, and only then reaches these pages.',
      'Everything here runs on a synthetic dataset (18,000 reservations across Tunisia’s 24 governorates). The method is real; the figures are not company results.',
    ],
  },
  {
    title: 'Four business questions',
    route: '/',
    spot: '.board',
    side: 'right',
    body: [
      'Each card asks one question a manager cares about: is the business making money, do bookings turn into business, are customers satisfied, does marketing spend pay off.',
      'It shows the key figure against the previous period and the trend behind it. The link on each card opens the detail.',
    ],
    actions: [{ kind: 'go', label: 'Open Revenue', to: '/revenue' }],
  },
  {
    title: 'Why you can trust the numbers',
    route: '/',
    spot: '.strip',
    side: 'right',
    body: [
      'Before a figure is shown, the data passes a quality gate: 15 checks on the star schema. This panel shows the result of the last run and what the source got wrong, such as ratings outside the 1–5 scale, and how each defect was handled.',
      'Nothing is dropped silently; every exclusion is counted and explained.',
    ],
    actions: [{ kind: 'go', label: 'Open Data quality', to: '/quality' }],
  },
  {
    title: 'Ask the analyst',
    spot: 'ez-assistant',
    side: 'left',
    body: [
      'Ask in plain language. The analyst checks the question, writes one read-only SQL SELECT against a semantic layer of the warehouse, runs it with a read-only database role, and shows the SQL it used so you can verify the answer.',
      'To protect the demo, each visitor can ask 8 questions every 10 minutes.',
    ],
    actions: [{ kind: 'ask', label: 'Ask a sample question', text: 'Which event type brings the most revenue?' }],
  },
  {
    title: 'Move around quickly',
    spot: '.search',
    side: 'right',
    body: [
      'Press Ctrl K (⌘ K on a Mac) to jump to a page, run a question worth asking, or ask anything.',
      'The ⓘ next to a figure opens how it is computed: definition, period and the rules that touched it.',
    ],
    actions: [{ kind: 'palette', label: 'Open the palette' }],
  },
  {
    title: 'How it is built',
    side: 'left',
    body: [
      'Source workbook → landing bucket → Airbyte → dbt (36 models, 43 tests) → Great Expectations gate → star schema in PostgreSQL → FastAPI → this Angular app, run daily by Airflow with Metabase, Prometheus and Grafana beside it.',
      'This live demo serves a snapshot of the warehouse built with the same dbt models and quality gate. The full stack runs with Docker Compose from the repository.',
    ],
    actions: [
      { kind: 'link', label: 'Read the code and architecture', href: REPO },
      { kind: 'link', label: 'About the author', href: PORTFOLIO },
    ],
  },
];

const SEEN = 'ez-tour-seen';

function seen(): boolean {
  try { return localStorage.getItem(SEEN) === '1'; } catch { return false; }
}
function markSeen(): void {
  try { localStorage.setItem(SEEN, '1'); } catch { /* private mode: the offer just shows again */ }
}

/**
 * A short guided tour for first-time visitors (recruiters, hiring managers): a non-modal card that stays beside the
 * page and outlines what it explains. Offered once, always available from the "Tour" key, and openable from any link
 * with ?tour=1.
 */
@Component({
  selector: 'ez-tour',
  imports: [Icon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (offer()) {
      <aside class="offer plate" aria-label="Guided tour">
        <p><strong>New here?</strong> A 60-second tour of what this shows and why you can trust it.</p>
        <div class="row">
          <button type="button" class="key primary" (click)="start()">Take the tour</button>
          <button type="button" class="key" (click)="dismissOffer()">Not now</button>
        </div>
      </aside>
    }

    <dialog #dlg class="card" [class.right]="step().side === 'right'" aria-labelledby="tour-title"
            aria-describedby="tour-body" (keydown)="keys($event)" (close)="onClosed()">
      <div class="top">
        <span class="mono count">Step {{ i() + 1 }} of {{ steps.length }}</span>
        <button type="button" class="x" aria-label="Close the tour" (click)="close()"><ez-icon name="close" [size]="16" /></button>
      </div>
      <h2 id="tour-title" #title tabindex="-1">{{ step().title }}</h2>
      <div id="tour-body" aria-live="polite">
        @for (p of step().body; track $index) { <p>{{ p }}</p> }
      </div>
      @if (step().actions; as acts) {
        <div class="acts">
          @for (a of acts; track a.label) { <button type="button" class="key" (click)="run(a)">{{ a.label }}</button> }
        </div>
      }
      <div class="foot">
        <button type="button" class="key" [disabled]="i() === 0" (click)="go(-1)">Back</button>
        <span class="dots" aria-hidden="true">@for (s of steps; track $index) { <i [class.on]="$index === i()"></i> }</span>
        @if (last()) {
          <button type="button" class="key primary" (click)="close()">Done</button>
        } @else {
          <button type="button" class="key primary" (click)="go(1)">Next<ez-icon name="right" [size]="14" /></button>
        }
      </div>
    </dialog>
  `,
  styles: `
    .offer { position: fixed; left: 1.25rem; bottom: 1.25rem; z-index: 35; width: min(22rem, calc(100vw - 2.5rem)); padding: 0.875rem 1rem;
      background: var(--plate-hover); border-color: var(--line-strong); box-shadow: 0 16px 40px rgb(0 0 0 / 0.45); font-size: 0.875rem; color: var(--ink-2); }
    .offer p { margin: 0 0 0.75rem; line-height: 1.5; }
    .offer strong { color: var(--ink); }
    .row, .acts, .foot { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }

    dialog.card { position: fixed; inset: auto auto 1.25rem 1.25rem; margin: 0; z-index: 40;
      width: min(27rem, calc(100vw - 2.5rem)); max-height: calc(100dvh - 2.5rem); overflow: auto; padding: 1rem 1.125rem 1.125rem;
      color: var(--ink-2); background: var(--plate-hover); border: 1px solid var(--line-strong); border-radius: var(--r-plate);
      box-shadow: 0 24px 60px rgb(0 0 0 / 0.55); }
    dialog.card.right { inset: auto 1.25rem 1.25rem auto; }
    .top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.375rem; }
    .count { font-size: 0.75rem; color: var(--ink-3); }
    .x { display: grid; place-items: center; width: 28px; height: 28px; border: 0; border-radius: 6px; background: none; color: var(--ink-3); cursor: pointer; }
    .x:hover { color: var(--ink); background: var(--plate); }
    h2 { margin: 0 0 0.5rem; font-size: 1.125rem; letter-spacing: -0.01em; color: var(--ink); outline: none; }
    #tour-body p { margin: 0 0 0.625rem; font-size: 0.9375rem; line-height: 1.55; }
    .acts { margin: 0.25rem 0 0.875rem; }
    .foot { justify-content: space-between; margin-top: 0.5rem; padding-top: 0.875rem; border-top: 1px solid var(--line); }
    .dots { display: inline-flex; gap: 0.375rem; }
    .dots i { width: 6px; height: 6px; border-radius: 50%; background: var(--line-strong); }
    .dots i.on { background: var(--data); }
    @media (max-width: 47.5rem) {
      dialog.card, dialog.card.right { inset: auto 0.75rem 0.75rem 0.75rem; width: auto; }
      .offer { left: 0.75rem; bottom: 0.75rem; }
    }
  `,
})
export class Tour implements OnInit {
  /** "Open the palette" asks the shell, which owns it */
  readonly palette = output<void>();

  private readonly router = inject(Router);
  private readonly store = inject(AssistantStore);
  private readonly dlg = viewChild.required<ElementRef<HTMLDialogElement>>('dlg');
  private readonly title = viewChild.required<ElementRef<HTMLElement>>('title');
  private spot: Element | null = null;

  protected readonly steps = STEPS;
  protected readonly i = signal(0);
  protected readonly step = computed(() => STEPS[this.i()]);
  protected readonly last = computed(() => this.i() === STEPS.length - 1);
  protected readonly offer = signal(false);
  private readonly open = signal(false);

  constructor() {
    effect(() => {
      const open = this.open();
      const step = this.step();
      if (!open) { this.clearSpot(); return; }
      if (step.route && this.router.url.split(/[?#]/)[0] !== step.route) void this.router.navigateByUrl(step.route);
      const index = this.i();
      // the page may still be rendering after a route change: outline once it has
      setTimeout(() => { if (this.open() && this.i() === index) this.setSpot(step.spot); }, step.route ? 400 : 0);
    });
  }

  ngOnInit(): void {
    if (typeof window === 'undefined') return;
    if (new URLSearchParams(location.search).get('tour') === '1') {
      history.replaceState(null, '', location.pathname + location.hash);
      setTimeout(() => this.start(), 600);
      return;
    }
    if (!seen()) setTimeout(() => { if (!this.open()) this.offer.set(true); }, 3000);
  }

  start(): void {
    this.offer.set(false);
    this.i.set(0);
    this.open.set(true);
    const d = this.dlg().nativeElement;
    if (!d.open) d.show();
    this.title().nativeElement.focus();
  }

  protected dismissOffer(): void { this.offer.set(false); markSeen(); }

  protected close(): void {
    const d = this.dlg().nativeElement;
    if (d.open) d.close();
    this.onClosed();
  }

  protected onClosed(): void { this.open.set(false); markSeen(); }

  protected go(delta: number): void {
    this.i.update((n) => Math.min(STEPS.length - 1, Math.max(0, n + delta)));
  }

  protected run(a: Action): void {
    switch (a.kind) {
      case 'go': void this.router.navigateByUrl(a.to); break;
      case 'ask': this.store.ask(a.text); break;
      case 'palette': this.palette.emit(); break;
      case 'link': window.open(a.href, '_blank', 'noopener'); break;
    }
  }

  protected keys(e: KeyboardEvent): void {
    if (e.key === 'Escape') { e.preventDefault(); this.close(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); this.go(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); this.go(-1); }
  }

  private setSpot(selector?: string): void {
    this.clearSpot();
    if (!selector) return;
    const el = document.querySelector(selector);
    if (!el) return;
    el.classList.add('tour-spot');
    this.spot = el;
    el.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }

  private clearSpot(): void {
    this.spot?.classList.remove('tour-spot');
    this.spot = null;
  }
}
