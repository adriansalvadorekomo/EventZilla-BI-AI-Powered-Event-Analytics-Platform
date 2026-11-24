import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/**
 * A headline figure, always shown settled: a figure that counts up passes through false values, and a manager
 * reading over a shoulder must never catch one.
 */
@Component({
  selector: 'ez-readout',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<span class="readout">{{ value() == null ? '–' : format()(value()!) }}</span>@if (unit()) {<span class="unit">{{ unit() }}</span>}`,
  styles: `:host { display: inline-flex; align-items: baseline; gap: 0.35rem; white-space: nowrap; }
           .unit { font-family: var(--mono); color: var(--ink-3); font-size: 0.875rem; }`,
})
export class Readout {
  readonly value = input<number | null | undefined>(null);
  readonly format = input<(n: number) => string>((n) => String(n));
  readonly unit = input('');
}
