import {
  ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterRenderEffect, computed, inject, signal, viewChild,
} from '@angular/core';
import gsap from 'gsap';
import { Answer, SuggestedQuestion, fmt } from '../api';
import { LineChart, Series } from '../charts/line-chart';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Icon } from '../ui/icon';
import { AssistantStore, COMMANDS, Msg, Stage } from './store';


const OBJECTIVES: Record<string, string> = {
  revenue: 'Revenue', reservations: 'Reservations', customers: 'Customers', marketing: 'Marketing', quality: 'Data quality',
};

const STARTERS = [
  'Which event type brings the most revenue?',
  'Which governorates earn the most per inhabitant?',
  'How did the confirmation rate change each year?',
];

const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

/** The analyst: plain questions in, checked answers out, with the work shown. */
@Component({
  selector: 'ez-assistant',
  imports: [Icon, LineChart, Outcomes],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './assistant.html',
  styleUrl: './assistant.css',
  host: { '[class.open]': 'store.open()' },
})
export class Assistant {
  protected readonly store = inject(AssistantStore);
  protected readonly starters = STARTERS;
  protected readonly objectives = OBJECTIVES;
  protected readonly draft = signal('');
  protected readonly menuIndex = signal(0);
  protected readonly elapsed = signal(0);
  private readonly log = viewChild.required<ElementRef<HTMLElement>>('log');
  private readonly input = viewChild.required<ElementRef<HTMLTextAreaElement>>('input');
  private animated = new Set<number>();

  protected readonly menu = computed(() => {
    const d = this.draft();
    if (!d.startsWith('/')) return [];
    return COMMANDS.filter((c) => c.name.startsWith(d.trim().toLowerCase()) || d === '/');
  });

  constructor() {
    let timer: ReturnType<typeof setInterval> | undefined;
    afterRenderEffect(() => {
      if (this.store.pending()) {
        if (!timer) { const t0 = performance.now(); timer = setInterval(() => this.elapsed.set((performance.now() - t0) / 1000), 100); }
      } else if (timer) { clearInterval(timer); timer = undefined; this.elapsed.set(0); }
    });
    inject(DestroyRef).onDestroy(() => timer && clearInterval(timer));

    // keep the newest message in view, and play each arrival once
    afterRenderEffect(() => {
      const msgs = this.store.messages();
      this.store.pending();
      const el = this.log().nativeElement;
      el.scrollTo({ top: el.scrollHeight, behavior: reduced() ? 'auto' : 'smooth' });
      for (const m of msgs) {
        if (this.animated.has(m.id)) continue;
        this.animated.add(m.id);
        const node = el.querySelector<HTMLElement>(`[data-msg="${m.id}"]`);
        if (node && !reduced()) this.play(m, node);
      }
    });
  }

  /** The signature moment: the answer replays the route it actually took, then the result lands. */
  private play(m: Msg, node: HTMLElement): void {
    const tl = gsap.timeline({ defaults: { ease: 'expo.out' } });
    const steps = node.querySelectorAll('.step');
    if (steps.length) {
      tl.from(steps, { opacity: 0, x: -8, duration: 0.35, stagger: 0.09 })
        .from(node.querySelectorAll('.step .mark'), { scale: 0, duration: 0.3, stagger: 0.09 }, '<');
    }
    if (m.kind === 'error') {
      tl.from(node.querySelectorAll('.step.stop .mark'), { scale: 1.8, duration: 0.45, ease: 'back.out(3)' }, '-=0.1')
        .from(node.querySelector('.msg-text'), { opacity: 0, y: 4, duration: 0.3 }, '-=0.2');
      return;
    }
    const text = node.querySelector('.msg-text');
    if (text) tl.fromTo(text, { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 0.7 }, steps.length ? '-=0.1' : 0);
    const viz = node.querySelector('.viz');
    if (viz) tl.from(viz, { opacity: 0, y: 8, filter: 'blur(4px)', duration: 0.5 }, '-=0.35');
    const items = node.querySelectorAll('.q');
    if (items.length) tl.from(items, { opacity: 0, y: 6, duration: 0.3, stagger: Math.min(0.035, 0.45 / items.length) }, 0);
    if (m.kind === 'you') tl.from(node, { opacity: 0, y: 6, duration: 0.25 }, 0);
  }

  protected send(text = this.draft()): void {
    this.store.submit(text);
    this.draft.set('');
    const el = this.input().nativeElement;
    el.value = '';
    el.style.height = '';
  }

  protected onKey(e: KeyboardEvent): void {
    const menu = this.menu();
    if (menu.length && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      this.menuIndex.update((i) => (i + (e.key === 'ArrowDown' ? 1 : -1) + menu.length) % menu.length);
      return;
    }
    if (menu.length && e.key === 'Tab') {
      e.preventDefault();
      this.draft.set(menu[this.menuIndex() % menu.length].name + ' ');
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (menu.length && menu[this.menuIndex() % menu.length].name !== this.draft().trim()) {
        return this.send(menu[this.menuIndex() % menu.length].name);
      }
      this.send();
    }
    if (e.key === 'Escape' && this.draft()) this.draft.set('');
  }

  protected onInput(el: HTMLTextAreaElement): void {
    this.draft.set(el.value);
    this.menuIndex.set(0);
    el.style.height = '';
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  }

  protected focusInput(): void {
    this.input().nativeElement.focus();
  }

  // ---- reading an answer ----

  protected viz(a: Answer): { kind: 'number'; label: string; value: string }
    | { kind: 'line'; labels: string[]; series: Series[]; format: (n: number) => string }
    | { kind: 'bars'; rows: Outcome[] }
    | { kind: 'table' } | null {
    if (!a.rows.length) return null;
    const numeric = (j: number) => a.rows.every((r) => r[j] == null || typeof r[j] === 'number');
    const yIdx = a.chart?.y ? a.columns.indexOf(a.chart.y) : a.columns.findIndex((_, j) => j > 0 && numeric(j));
    const xIdx = a.chart?.x ? a.columns.indexOf(a.chart.x) : 0;
    if (a.rows.length === 1 && (a.columns.length === 1 || a.chart?.type === 'number')) {
      const j = a.columns.findIndex((_, k) => numeric(k));
      if (j >= 0) return { kind: 'number', label: a.columns[j], value: this.num(a.rows[0][j] as number, a, j) };
    }
    if (yIdx < 0 || xIdx < 0 || !numeric(yIdx) || a.columns.length > 4) return { kind: 'table' };
    const ys = a.rows.map((r) => r[yIdx] as number);
    if (a.chart?.type === 'line' && a.rows.length > 2) {
      return { kind: 'line', labels: a.rows.map((r) => String(r[xIdx])), format: (n) => this.num(n, a, yIdx),
        series: [{ name: a.columns[yIdx], values: ys, fill: true }] };
    }
    if (a.chart?.type === 'table') return { kind: 'table' };
    const max = Math.max(...ys.map(Math.abs), 1e-9);
    return { kind: 'bars', rows: a.rows.slice(0, 12).map((r, i) => ({
      label: String(r[xIdx]), value: this.num(ys[i], a, yIdx), bar: Math.abs(ys[i]) / max, tone: i === 0 ? 'data' : 'muted',
    })) };
  }

  protected cell(v: string | number | null, a: Answer, j: number): string {
    return typeof v === 'number' ? this.num(v, a, j) : (v ?? '–');
  }

  private num(v: number, a: Answer, j: number): string {
    if (v == null) return '–';
    const col = a.columns[j]?.toLowerCase() ?? '';
    if (/year/.test(col) && Number.isInteger(v)) return String(v);
    if (Math.abs(v) >= 10000) return fmt.compact(v);
    return Number.isInteger(v) ? fmt.whole(v) : v.toFixed(2);
  }

  protected grouped(items: SuggestedQuestion[], topic: string | null): [string, SuggestedQuestion[]][] {
    const out = new Map<string, SuggestedQuestion[]>();
    for (const q of items) {
      if (topic && q.objective !== topic) continue;
      out.set(q.objective, [...(out.get(q.objective) ?? []), q]);
    }
    return [...out.entries()];
  }

  protected readonly commands = COMMANDS;
  protected readonly elapsedText = computed(() => this.elapsed().toFixed(1));
}
