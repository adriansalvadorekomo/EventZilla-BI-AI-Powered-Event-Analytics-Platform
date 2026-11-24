import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export interface Outcome {
  label: string;
  /** formatted main figure, right-aligned */
  value: string;
  /** bar length, 0..1 */
  bar: number;
  sub?: string;
  /** secondary figure, under the main one */
  aside?: string;
  tone?: 'data' | 'muted' | 'gate' | 'down';
}

/** Ranked outcomes, the way a market lists its outcomes: name, bar, figure. */
@Component({
  selector: 'ez-outcomes',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ol class="rows" [attr.aria-label]="label()">
      @for (r of rows(); track r.label; let i = $index) {
        <li class="row" [style.--i]="i">
          <div class="name">
            <span class="title">{{ r.label }}</span>
            @if (r.sub) { <span class="sub">{{ r.sub }}</span> }
          </div>
          <div class="track" aria-hidden="true"><span class="bar" [class]="'bar ' + (r.tone ?? 'data')" [style.--w]="r.bar"></span></div>
          <div class="fig">
            <span class="num">{{ r.value }}</span>
            @if (r.aside) { <span class="num aside">{{ r.aside }}</span> }
          </div>
        </li>
      }
    </ol>
  `,
  styles: `
    .rows { list-style: none; margin: 0; padding: 0; display: grid; }
    .row {
      display: grid; grid-template-columns: minmax(7rem, 1.1fr) minmax(4rem, 1.4fr) minmax(5.5rem, auto);
      align-items: center; gap: 0.875rem; padding: 0.625rem 0; border-top: 1px solid var(--line);
    }
    .row:first-child { border-top: 0; }
    .name { display: grid; min-width: 0; }
    .title { font-weight: 600; font-size: 0.875rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .sub { color: var(--ink-3); font-size: 0.75rem; }
    .track { height: 6px; background: var(--display); border-radius: 3px; overflow: hidden; }
    .bar {
      display: block; height: 100%; width: calc(var(--w) * 100%); border-radius: 3px; transform-origin: left;
      animation: grow 700ms var(--ease-out) both; animation-delay: calc(var(--i) * 40ms);
    }
    .bar.data { background: var(--data); }
    .bar.muted { background: var(--series-2); }
    .bar.gate { background: var(--gate); }
    .bar.down { background: var(--down); }
    .fig { display: grid; justify-items: end; font-size: 0.875rem; }
    .aside { color: var(--ink-3); font-size: 0.75rem; }
    @keyframes grow { from { transform: scaleX(0); } }
    @media (max-width: 30rem) { .row { grid-template-columns: 1fr auto; } .track { grid-column: 1 / -1; grid-row: 2; } }
  `,
})
export class Outcomes {
  readonly rows = input.required<Outcome[]>();
  readonly label = input('');
}
