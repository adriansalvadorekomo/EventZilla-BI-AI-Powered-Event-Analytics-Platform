import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { fmt } from '../api';
import { Icon } from './icon';

/** A change against a reference period, coloured by whether it is good news, with its size in words when small. */
@Component({
  selector: 'ez-change',
  imports: [Icon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="change" [class]="'change ' + tone()">
      <ez-icon [name]="dir()" [size]="12" />{{ text() }}
    </span>
    <span class="ref">{{ against() }}@if (small()) { · small }</span>
  `,
  styles: `
    :host { display: inline-flex; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; }
    .ref { color: var(--ink-3); font-size: 0.8125rem; }
  `,
})
export class Change {
  readonly value = input.required<number>();
  /** pct: relative change; pts: percentage points; abs: plain difference (a rating) */
  readonly unit = input<'pct' | 'pts' | 'abs'>('pct');
  readonly against = input('');
  /** which direction is good news (lower cost is good) */
  readonly good = input<'up' | 'down'>('up');
  /** below this size the change is called small */
  readonly smallBelow = input(5);

  protected readonly dir = computed(() => (Math.abs(this.value()) < 0.05 ? 'flat' : this.value() > 0 ? 'up' : 'down'));
  protected readonly tone = computed(() => {
    if (this.dir() === 'flat') return 'flat';
    // green is good news and red bad news; the arrow carries the direction (a cost that falls is green)
    return (this.value() > 0) === (this.good() === 'up') ? 'up' : 'down';
  });
  protected readonly small = computed(() => Math.abs(this.value()) < this.smallBelow());
  protected readonly text = computed(() => {
    const u = this.unit();
    return u === 'pct' ? fmt.signedPct(this.value()) : u === 'pts' ? fmt.signedPts(this.value()) : fmt.signedAbs(this.value());
  });
}
