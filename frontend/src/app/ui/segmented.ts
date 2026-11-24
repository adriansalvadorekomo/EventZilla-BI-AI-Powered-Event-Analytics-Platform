import {
  ChangeDetectionStrategy, Component, ElementRef, afterRenderEffect, input, model, signal, viewChildren,
} from '@angular/core';

export interface Segment { id: string; label: string; }

/** A segmented control whose thumb slides to the chosen segment. Arrow keys move the choice (radio group). */
@Component({
  selector: 'ez-segmented',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="seg" role="radiogroup" [attr.aria-label]="label()">
      <span class="thumb" aria-hidden="true" [style.transform]="'translateX(' + thumb().x + 'px) scaleX(' + thumb().w / 100 + ')'"></span>
      @for (o of options(); track o.id; let i = $index) {
        <button #b type="button" role="radio" [attr.aria-checked]="o.id === value()" [tabindex]="o.id === value() ? 0 : -1"
                (click)="value.set(o.id)" (keydown)="onKey($event, i)">{{ o.label }}</button>
      }
    </div>
  `,
  styles: `
    .seg { position: relative; display: inline-flex; padding: 3px; gap: 2px; background: var(--display); border: 1px solid var(--line); border-radius: 8px; }
    .thumb { position: absolute; top: 3px; bottom: 3px; left: 0; width: 100px; transform-origin: left; background: var(--line-strong); border-radius: 6px; transition: transform 260ms var(--ease-out); }
    button { position: relative; z-index: 1; height: 28px; padding: 0 0.75rem; border: 0; background: none; cursor: pointer; border-radius: 6px;
      font-family: var(--sans); font-size: 0.8125rem; font-weight: 600; color: var(--ink-3); transition: color 160ms var(--ease-out); white-space: nowrap; }
    button:hover { color: var(--ink-2); }
    button[aria-checked='true'] { color: var(--ink); }
  `,
})
export class Segmented {
  readonly options = input.required<Segment[]>();
  readonly value = model.required<string>();
  readonly label = input('');
  private readonly buttons = viewChildren<ElementRef<HTMLButtonElement>>('b');
  /** the thumb is a 100 px bar moved and scaled with transforms only */
  protected readonly thumb = signal({ x: 3, w: 0 });

  constructor() {
    afterRenderEffect(() => {
      const i = this.options().findIndex((o) => o.id === this.value());
      const b = this.buttons()[i]?.nativeElement;
      if (b) this.thumb.set({ x: b.offsetLeft, w: b.offsetWidth });
    });
  }

  protected onKey(e: KeyboardEvent, i: number): void {
    const n = this.options().length;
    const step = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const next = (i + step + n) % n;
    this.value.set(this.options()[next].id);
    this.buttons()[next]?.nativeElement.focus();
  }
}
