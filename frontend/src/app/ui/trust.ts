import { ChangeDetectionStrategy, Component, ElementRef, input, viewChild } from '@angular/core';
import { Icon } from './icon';

let uid = 0;

/** "How this is computed": a popover on every headline figure with its definition, period and the rules applied. */
@Component({
  selector: 'ez-trust',
  imports: [Icon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button #btn type="button" class="tbtn" [attr.popovertarget]="id" [attr.aria-label]="'How ' + subject() + ' is computed'" (click)="place()">
      <ez-icon name="info" [size]="14" />
    </button>
    <div #pop class="pop" [id]="id" popover role="note">
      <div class="label">How this is computed</div>
      <ng-content />
    </div>
  `,
  styles: `
    :host { display: inline-flex; vertical-align: middle; }
    .tbtn { display: inline-grid; place-items: center; width: 22px; height: 22px; border: 0; border-radius: 50%; background: none; color: var(--ink-3); cursor: pointer; }
    .tbtn:hover { color: var(--ink); background: var(--plate-hover); }
    .pop {
      position: fixed; inset: auto; margin: 0; width: min(20rem, calc(100vw - 2rem)); padding: 0.75rem 0.875rem;
      background: var(--plate-hover); color: var(--ink-2); border: 1px solid var(--line-strong); border-radius: 8px;
      box-shadow: 0 16px 40px rgb(0 0 0 / 0.5); font-size: 0.8125rem; line-height: 1.55;
      opacity: 0; transform: translateY(4px); transition: opacity 160ms var(--ease-out), transform 160ms var(--ease-out), overlay 160ms allow-discrete, display 160ms allow-discrete;
    }
    .pop:popover-open { opacity: 1; transform: none; }
    @starting-style { .pop:popover-open { opacity: 0; transform: translateY(4px); } }
    .pop .label { margin-bottom: 0.375rem; }
  `,
})
export class Trust {
  readonly subject = input('this figure');
  protected readonly id = `trust-${++uid}`;
  private readonly btn = viewChild.required<ElementRef<HTMLButtonElement>>('btn');
  private readonly pop = viewChild.required<ElementRef<HTMLElement>>('pop');

  protected place(): void {
    const r = this.btn().nativeElement.getBoundingClientRect();
    const p = this.pop().nativeElement;
    const width = Math.min(320, innerWidth - 32);
    p.style.left = `${Math.max(16, Math.min(r.left - 12, innerWidth - width - 16))}px`;
    p.style.top = `${r.bottom + 8}px`;
  }
}
