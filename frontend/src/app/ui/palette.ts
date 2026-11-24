import {
  ChangeDetectionStrategy, Component, ElementRef, computed, inject, signal, viewChild,
} from '@angular/core';
import { Router } from '@angular/router';
import gsap from 'gsap';
import { SuggestedQuestion } from '../api';
import { AssistantStore } from '../assistant/store';
import { Icon } from './icon';

interface Item { kind: 'page' | 'question' | 'ask'; label: string; detail?: string; run: () => void; }

export const PAGES = [
  { path: '/', label: 'Board', detail: 'every objective at a glance' },
  { path: '/revenue', label: 'Revenue', detail: 'is the business making money, and where from' },
  { path: '/reservations', label: 'Reservations', detail: 'how many bookings turn into business' },
  { path: '/customers', label: 'Customers', detail: 'satisfaction, loyalty, complaints' },
  { path: '/marketing', label: 'Marketing', detail: 'does spend bring customers' },
  { path: '/quality', label: 'Data quality', detail: 'what was left out, and why' },
];

/** Ctrl/⌘ K: go to a page, run a question worth asking, or ask anything. */
@Component({
  selector: 'ez-palette',
  imports: [Icon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { '(document:keydown)': 'onGlobalKey($event)' },
  template: `
    <dialog #dlg class="palette" aria-label="Go to or ask" (close)="query.set('')" (click)="onBackdrop($event)">
      <div class="box" #box>
        <div class="search">
          <ez-icon name="ask" [size]="16" />
          <input #q type="text" [value]="query()" (input)="query.set(q.value); active.set(0)" (keydown)="onKey($event)"
                 placeholder="Go to a page, or ask a question" aria-label="Go to a page, or ask a question"
                 role="combobox" aria-expanded="true" aria-controls="palette-list" [attr.aria-activedescendant]="'pi-' + active()" />
          <kbd class="mono">esc</kbd>
        </div>
        <ul id="palette-list" role="listbox" class="list">
          @for (it of items(); track it.label; let i = $index) {
            @if (i === 0 || items()[i - 1].kind !== it.kind) { <li class="sect" role="presentation">{{ sect(it.kind) }}</li> }
            <li [id]="'pi-' + i" role="option" [attr.aria-selected]="i === active()" [class.on]="i === active()"
                (mousemove)="active.set(i)" (click)="choose(it)">
              <span class="it-label">{{ it.label }}</span>
              @if (it.detail) { <span class="it-detail" [class.value]="it.kind === 'question'">{{ it.detail }}</span> }
            </li>
          }
        </ul>
      </div>
    </dialog>
  `,
  styles: `
    .palette { padding: 0; border: 0; background: none; width: min(40rem, calc(100vw - 2rem)); margin-top: 12vh; color: var(--ink); overflow: visible; }
    .palette::backdrop { background: rgb(5 9 18 / 0.6); backdrop-filter: blur(3px); }
    .box { background: var(--plate); border: 1px solid var(--line-strong); border-radius: var(--r-plate); box-shadow: 0 24px 64px rgb(0 0 0 / 0.55); overflow: hidden; }
    .search { display: flex; align-items: center; gap: 0.625rem; padding: 0 1rem; border-bottom: 1px solid var(--line); color: var(--ink-3); }
    input { flex: 1; height: 52px; border: 0; background: none; color: var(--ink); font: inherit; font-size: 1rem; caret-color: var(--data); }
    input:focus { outline: none; }
    input::placeholder { color: var(--ink-3); }
    kbd { font-size: 0.6875rem; border: 1px solid var(--line-strong); border-radius: 4px; padding: 0.1rem 0.35rem; }
    .list { list-style: none; margin: 0; padding: 0.375rem; max-height: min(60vh, 28rem); overflow-y: auto; }
    .sect { padding: 0.625rem 0.625rem 0.25rem; font-size: 0.75rem; font-weight: 650; color: var(--ink-3); }
    li[role='option'] { display: grid; gap: 0.125rem; padding: 0.5rem 0.625rem; border-radius: 6px; cursor: pointer; }
    li.on { background: var(--plate-hover); box-shadow: inset 2px 0 0 var(--data); }
    .it-label { font-weight: 600; font-size: 0.875rem; }
    .it-detail { color: var(--ink-3); font-size: 0.75rem; }
    .it-detail.value { color: var(--data-ink); }
  `,
})
export class Palette {
  private readonly router = inject(Router);
  private readonly store = inject(AssistantStore);
  private readonly dlg = viewChild.required<ElementRef<HTMLDialogElement>>('dlg');
  private readonly box = viewChild.required<ElementRef<HTMLElement>>('box');
  private readonly input = viewChild.required<ElementRef<HTMLInputElement>>('q');
  protected readonly query = signal('');
  protected readonly active = signal(0);
  private readonly questions = signal<SuggestedQuestion[]>([]);

  protected readonly items = computed<Item[]>(() => {
    const q = this.query().trim().toLowerCase();
    const match = (s: string) => !q || s.toLowerCase().includes(q);
    const pages: Item[] = PAGES.filter((p) => match(p.label) || match(p.detail))
      .map((p) => ({ kind: 'page', label: p.label, detail: p.detail, run: () => this.router.navigateByUrl(p.path) }));
    const qs: Item[] = this.questions().filter((x) => match(x.question))
      .slice(0, q ? 8 : 5)
      .map((x) => ({ kind: 'question', label: x.question, detail: x.value ?? undefined, run: () => this.store.ask(x.question) }));
    const ask: Item[] = q.length > 2 ? [{ kind: 'ask', label: `Ask the analyst: “${this.query().trim()}”`, run: () => this.store.ask(this.query().trim()) }] : [];
    return [...pages, ...qs, ...ask];
  });

  open(): void {
    const d = this.dlg().nativeElement;
    if (d.open) return;
    if (!this.questions().length) this.store.loadQuestions((items) => this.questions.set(items), true);
    d.showModal();
    this.active.set(0);
    this.input().nativeElement.focus();
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
      gsap.fromTo(this.box().nativeElement, { opacity: 0, y: -6 }, { opacity: 1, y: 0, duration: 0.18, ease: 'expo.out' });
    }
  }

  protected sect(kind: Item['kind']): string {
    return kind === 'page' ? 'Pages' : kind === 'question' ? 'Questions worth asking, with today\'s answer' : 'Ask the analyst';
  }

  protected choose(it: Item): void {
    this.dlg().nativeElement.close();
    it.run();
  }

  protected onKey(e: KeyboardEvent): void {
    const n = this.items().length;
    if (!n) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      this.active.update((i) => (i + (e.key === 'ArrowDown' ? 1 : -1) + n) % n);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      this.choose(this.items()[this.active()]);
    }
  }

  protected onGlobalKey(e: KeyboardEvent): void {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); this.open(); }
  }

  protected onBackdrop(e: MouseEvent): void {
    if (e.target === this.dlg().nativeElement) this.dlg().nativeElement.close();
  }
}
