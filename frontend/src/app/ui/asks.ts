import { ChangeDetectionStrategy, Component, inject, input, signal } from '@angular/core';
import { SuggestedQuestion } from '../api';
import { AssistantStore } from '../assistant/store';
import { Icon } from './icon';

/** The questions worth asking about this page: today's answer, the decision it informs, one click to the analyst. */
@Component({
  selector: 'ez-asks',
  imports: [Icon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="plate panel" [attr.aria-labelledby]="'asks-' + objective()">
      <div class="section-head">
        <h2 [id]="'asks-' + objective()">Questions to decide on</h2>
        <p>Today's answer from the warehouse. Select one to have the analyst explain it.</p>
      </div>
      <div class="asks">
        @for (q of items(); track q.id) {
          <button type="button" class="ask" (click)="store.ask(q.question)">
            <span class="q">{{ q.question }}</span>
            <span class="v">{{ q.value ?? 'not available' }}</span>
            <span class="d">Decides: {{ q.decision }}</span>
            <ez-icon name="right" [size]="14" class="go" />
          </button>
        } @empty {
          @for (i of [1, 2, 3]; track i) { <span class="skeleton sk"></span> }
        }
      </div>
    </section>
  `,
  styles: `
    .asks { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 22rem), 1fr)); column-gap: 1.5rem; }
    .ask {
      position: relative; display: grid; align-content: start; gap: 0.25rem; text-align: left; cursor: pointer;
      padding: 0.875rem 2.25rem 0.875rem 0.5rem; margin: 0 -0.5rem; background: none; border: 0; border-top: 1px solid var(--line); border-radius: 0;
      transition: background-color 140ms var(--ease-out);
    }
    .ask:hover { background: var(--plate-hover); }
    .q { font-weight: 650; font-size: 0.875rem; color: var(--ink); }
    .v { color: var(--data-ink); font-size: 0.8125rem; font-weight: 560; }
    .d { color: var(--ink-3); font-size: 0.75rem; }
    
    .go { position: absolute; right: 0.75rem; top: 0.9rem; color: var(--ink-3); transition: transform 160ms var(--ease-out), color 140ms; }
    .ask:hover .go { transform: translateX(2px); color: var(--data-ink); }
    .sk { height: 6.5rem; }
  `,
})
export class Asks {
  readonly objective = input.required<SuggestedQuestion['objective']>();
  protected readonly store = inject(AssistantStore);
  protected readonly items = signal<SuggestedQuestion[]>([]);

  constructor() {
    queueMicrotask(() => this.store.loadQuestions((all) => this.items.set(all.filter((q) => q.objective === this.objective())), true));
  }
}
