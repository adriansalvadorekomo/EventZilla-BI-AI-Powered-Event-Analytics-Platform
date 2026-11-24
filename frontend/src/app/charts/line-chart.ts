import {
  ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterRenderEffect, computed, inject, input, model, signal,
} from '@angular/core';
import gsap from 'gsap';

export interface Series {
  name: string;
  values: (number | null)[];
  color?: string;
  dashed?: boolean;
  fill?: boolean;
}

const reduced = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

function niceStep(raw: number): number {
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const n = raw / mag;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * mag;
}

/**
 * A market-style line chart: values on the right, a crosshair that scrubs every series at once, the readout in the
 * legend. The value axis starts at zero unless a domain is given: on this flat, synthetic data a cropped axis would
 * turn noise into drama.
 */
@Component({
  selector: 'ez-line-chart',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (legend()) {
      <div class="legend" aria-hidden="true">
        @for (s of series(); track s.name) {
          <span class="lg">
            <i [class.dash]="s.dashed" [style.--c]="s.color ?? 'var(--data)'"></i>
            <span class="lg-name">{{ s.name }}</span>
            <b class="num">{{ show(hover() === null ? latest(s) : s.values[readIndex()]) }}</b>
          </span>
        }
        <span class="when num">{{ labels()[readIndex()] ? formatX()(labels()[readIndex()]) : '' }}</span>
      </div>
    }
    <svg [attr.width]="w()" [attr.height]="height()" [attr.viewBox]="'0 0 ' + w() + ' ' + height()"
         role="img" [attr.aria-label]="summary()" tabindex="0"
         (pointermove)="onMove($event)" (pointerleave)="hover.set(null)" (blur)="hover.set(null)"
         (keydown)="onKey($event)">
      @if (!compact()) {
        @for (t of ticks(); track t) {
          <line class="grid" [attr.x1]="pad().l" [attr.x2]="w() - pad().r" [attr.y1]="y(t)" [attr.y2]="y(t)" />
          <text class="ytick" [attr.x]="w() - pad().r + 8" [attr.y]="y(t) + 4">{{ format()(t) }}</text>
        }
        @for (i of xTickIdx(); track i) {
          <text class="xtick" [attr.x]="x(i)" [attr.y]="height() - 6" [attr.text-anchor]="i === 0 ? 'start' : i === labels().length - 1 ? 'end' : 'middle'">{{ formatX()(labels()[i]) }}</text>
        }
      } @else {
        <line class="grid" [attr.x1]="0" [attr.x2]="w()" [attr.y1]="y(domain()[0])" [attr.y2]="y(domain()[0])" />
      }
      @for (s of series(); track s.name; let k = $index) {
        @if (s.fill) { <path class="area" [attr.d]="area(s)" [style.--c]="s.color ?? 'var(--data)'" /> }
        <path class="ln" [class.dashed]="s.dashed" [attr.d]="path(s)" [style.--c]="s.color ?? 'var(--data)'"
              [attr.pathLength]="s.dashed ? null : 1" [attr.stroke-width]="compact() ? 1.75 : 2" />
      }
      @if (hover() !== null) {
        <line class="cross" [attr.x1]="x(hover()!)" [attr.x2]="x(hover()!)" [attr.y1]="pad().t" [attr.y2]="height() - pad().b" />
        @for (s of series(); track s.name) {
          @if (s.values[hover()!] != null) {
            <circle class="dot" [attr.cx]="x(hover()!)" [attr.cy]="y(s.values[hover()!]!)" r="4" [style.--c]="s.color ?? 'var(--data)'" />
          }
        }
      } @else if (end(); as e) {
        <circle class="dot end" [attr.cx]="e.x" [attr.cy]="e.y" r="3.5" [style.--c]="series()[0].color ?? 'var(--data)'" />
      }
    </svg>
    <table class="sr-only">
      <caption>{{ summary() }}</caption>
      <tr><th scope="col">Period</th>@for (s of series(); track s.name) {<th scope="col">{{ s.name }}</th>}</tr>
      @for (l of labels(); track $index; let i = $index) {
        <tr><th scope="row">{{ formatX()(l) }}</th>@for (s of series(); track s.name) {<td>{{ show(s.values[i]) }}</td>}</tr>
      }
    </table>
  `,
  styles: `
    :host { display: block; position: relative; min-width: 0; }
    svg { display: block; overflow: visible; touch-action: pan-y; cursor: crosshair; }
    svg:focus-visible { outline: 2px solid var(--data); outline-offset: 4px; }
    .legend { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 1rem; margin-bottom: 0.625rem; font-size: 0.8125rem; color: var(--ink-2); min-height: 1.3rem; }
    .lg { display: inline-flex; align-items: baseline; gap: 0.4rem; }
    .lg i { width: 10px; height: 2px; background: var(--c); align-self: center; border-radius: 1px; }
    .lg i.dash { height: 0; background: none; border-top: 2px dashed var(--c); }
    .lg b { color: var(--ink); font-weight: 560; }
    .when { margin-left: auto; color: var(--ink-3); font-size: 0.75rem; }
    .grid { stroke: var(--line); stroke-width: 1; }
    .ytick, .xtick { fill: var(--ink-3); font-family: var(--mono); font-size: 10.5px; font-variant-numeric: tabular-nums; }
    .ln { fill: none; stroke: var(--c); stroke-linejoin: round; stroke-linecap: round; }
    .ln.dashed { stroke-dasharray: 4 4; opacity: 0.85; }
    .area { fill: var(--c); opacity: 0.09; }
    .cross { stroke: var(--ink-3); stroke-width: 1; stroke-dasharray: 2 3; }
    .dot { fill: var(--display); stroke: var(--c); stroke-width: 2; }
    .dot.end { fill: var(--c); stroke: var(--display); stroke-width: 2; }
  `,
})
export class LineChart {
  readonly labels = input.required<string[]>();
  readonly series = input.required<Series[]>();
  readonly height = input(220);
  readonly compact = input(false);
  readonly legend = input(true);
  readonly fixedDomain = input<[number, number] | null>(null, { alias: 'domain' });
  readonly format = input<(n: number) => string>((n) => String(n));
  readonly formatX = input<(s: string) => string>((s) => s);
  readonly summary = input('');
  /** trace the lines in on arrival: kept for the board's first load and the analyst's results */
  readonly animate = input(false);
  /** Hovered index; two-way so charts that share an axis scrub together. */
  readonly hover = model<number | null>(null);

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  protected readonly w = signal(600);
  private drawnFor: unknown = null;

  protected readonly pad = computed(() =>
    this.compact() ? { l: 2, r: 2, t: 6, b: 4 } : { l: 0, r: 58, t: 8, b: 24 });

  protected readonly domain = computed<[number, number]>(() => {
    const fixed = this.fixedDomain();
    const vals = this.series().flatMap((s) => s.values).filter((v): v is number => v != null && Number.isFinite(v));
    const max = vals.length ? Math.max(...vals) : 1;
    if (fixed) return fixed;
    const lo = Math.min(0, ...vals);
    const step = niceStep((max - lo) / 4);
    return [Math.floor(lo / step) * step, Math.ceil(max / step) * step || 1];
  });

  protected readonly ticks = computed(() => {
    const [lo, hi] = this.domain();
    const step = niceStep((hi - lo) / 4);
    const out: number[] = [];
    for (let t = lo; t <= hi + step / 1e6; t += step) out.push(+t.toFixed(10));
    return out;
  });

  protected readonly xTickIdx = computed(() => {
    const n = this.labels().length;
    const want = Math.max(2, Math.min(6, Math.floor(this.w() / 110)));
    if (n <= want) return [...Array(n).keys()];
    return [...Array(want).keys()].map((k) => Math.round((k * (n - 1)) / (want - 1)));
  });

  protected readonly readIndex = computed(() => {
    const h = this.hover();
    if (h !== null) return h;
    const first = this.series()[0]?.values ?? [];
    for (let i = first.length - 1; i >= 0; i--) if (first[i] != null) return i;
    return 0;
  });

  protected readonly end = computed(() => {
    const s = this.series()[0];
    if (!s) return null;
    const i = this.readIndex();
    const v = s.values[i];
    return v == null ? null : { x: this.x(i), y: this.y(v) };
  });

  constructor() {
    const ro = new ResizeObserver(([e]) => this.w.set(Math.max(160, Math.floor(e.contentRect.width))));
    ro.observe(this.host.nativeElement);
    inject(DestroyRef).onDestroy(() => ro.disconnect());

    // the draw-in: once per dataset, solid lines trace from left to right
    afterRenderEffect(() => {
      const data = this.series();
      if (!data.length || this.drawnFor === data) return;
      this.drawnFor = data;
      if (!this.animate()) return;
      const paths = this.host.nativeElement.querySelectorAll<SVGPathElement>('path.ln:not(.dashed)');
      if (reduced() || !paths.length) return;
      gsap.fromTo(paths, { strokeDasharray: 1, strokeDashoffset: 1 },
        { strokeDashoffset: 0, duration: 0.9, ease: 'expo.out', stagger: 0.08,
          onComplete: () => paths.forEach((p) => { p.style.strokeDasharray = ''; p.style.strokeDashoffset = ''; }) });
    });
  }

  protected x(i: number): number {
    const { l, r } = this.pad();
    const n = this.labels().length;
    return n <= 1 ? l : l + (i * (this.w() - l - r)) / (n - 1);
  }

  protected y(v: number): number {
    const { t, b } = this.pad();
    const [lo, hi] = this.domain();
    return t + (1 - (v - lo) / (hi - lo || 1)) * (this.height() - t - b);
  }

  protected path(s: Series): string {
    let d = '';
    let pen = false;
    s.values.forEach((v, i) => {
      if (v == null) { pen = false; return; }
      d += `${pen ? 'L' : 'M'}${this.x(i).toFixed(1)},${this.y(v).toFixed(1)}`;
      pen = true;
    });
    return d;
  }

  protected area(s: Series): string {
    const idx = s.values.map((v, i) => (v == null ? -1 : i)).filter((i) => i >= 0);
    if (idx.length < 2) return '';
    const base = this.y(Math.max(this.domain()[0], 0));
    return `${this.path(s)}L${this.x(idx.at(-1)!).toFixed(1)},${base}L${this.x(idx[0]).toFixed(1)},${base}Z`;
  }

  protected latest(s: Series): number | null {
    for (let i = s.values.length - 1; i >= 0; i--) if (s.values[i] != null) return s.values[i];
    return null;
  }

  protected show(v: number | null | undefined): string {
    return v == null ? '–' : this.format()(v);
  }

  protected onMove(e: PointerEvent): void {
    const svg = e.currentTarget as SVGSVGElement;
    const px = e.clientX - svg.getBoundingClientRect().left;
    const n = this.labels().length;
    const { l, r } = this.pad();
    const i = Math.round(((px - l) / (this.w() - l - r)) * (n - 1));
    this.hover.set(Math.min(n - 1, Math.max(0, i)));
  }

  protected onKey(e: KeyboardEvent): void {
    const n = this.labels().length;
    const cur = this.hover() ?? this.readIndex();
    const next = e.key === 'ArrowLeft' ? cur - 1 : e.key === 'ArrowRight' ? cur + 1
      : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : null;
    if (next === null) return;
    e.preventDefault();
    this.hover.set(Math.min(n - 1, Math.max(0, next)));
  }
}
