import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { Answer, SuggestedQuestion } from '../api';

export type Stage = 'screen' | 'guard' | 'run' | 'busy' | 'model' | 'config' | 'network';

export type Msg =
  | { id: number; kind: 'you'; text: string }
  | { id: number; kind: 'answer'; data: Answer }
  | { id: number; kind: 'error'; stage: Stage; message: string }
  | { id: number; kind: 'questions'; items: SuggestedQuestion[]; topic: string | null }
  | { id: number; kind: 'help' };

/** a message before it gets its id (Omit, distributed over the union) */
type NewMsg = Msg extends infer M ? (M extends Msg ? Omit<M, 'id'> : never) : never;

export const COMMANDS = [
  { name: '/questions', hint: 'questions worth asking now, with their answer and the decision each informs' },
  { name: '/questions revenue', hint: 'only one objective: revenue, reservations, customers, marketing or quality' },
  { name: '/help', hint: 'what the analyst can do' },
  { name: '/clear', hint: 'clear the conversation' },
];

const TOPICS = ['revenue', 'reservations', 'customers', 'marketing', 'quality'];

/** Conversation state for the analyst, shared so any page can ask it a question. */
@Injectable({ providedIn: 'root' })
export class AssistantStore {
  private readonly http = inject(HttpClient);
  private seq = 0;
  private questionCache: SuggestedQuestion[] | null = null;
  private inflight: Observable<SuggestedQuestion[]> | null = null;

  readonly messages = signal<Msg[]>([]);
  readonly pending = signal(false);
  /** the sheet on small screens */
  readonly open = signal(false);

  submit(raw: string): void {
    const text = raw.trim();
    if (!text || this.pending()) return;
    if (text.startsWith('/')) return this.command(text);
    this.ask(text);
  }

  ask(question: string): void {
    if (this.pending()) return;
    this.open.set(true);
    this.push({ kind: 'you', text: question });
    this.pending.set(true);
    this.http.post<Answer>('/api/ask', { question }).subscribe({
      next: (data) => { this.pending.set(false); this.push({ kind: 'answer', data }); },
      error: (e: HttpErrorResponse) => { this.pending.set(false); this.push({ kind: 'error', ...describe(e) }); },
    });
  }

  command(text: string): void {
    const [cmd, arg] = text.toLowerCase().split(/\s+/, 2);
    if (cmd === '/clear') { this.messages.set([]); return; }
    this.push({ kind: 'you', text });
    if (cmd === '/help') { this.push({ kind: 'help' }); return; }
    if (cmd === '/questions') {
      const topic = arg && TOPICS.includes(arg) ? arg : null;
      this.loadQuestions((items) => this.push({ kind: 'questions', items, topic }));
      return;
    }
    this.push({ kind: 'error', stage: 'model', message: `Unknown command ${cmd}. Type /help for the commands.` });
  }

  /** quiet: for pages and the palette, which load in the background and must not show the analyst working */
  loadQuestions(then: (items: SuggestedQuestion[]) => void, quiet = false): void {
    if (this.questionCache) return then(this.questionCache);
    if (!quiet) this.pending.set(true);
    this.inflight ??= this.http.get<SuggestedQuestion[]>('/api/questions').pipe(shareReplay(1));
    this.inflight.subscribe({
      next: (items) => { if (!quiet) this.pending.set(false); this.questionCache = items; then(items); },
      error: (e: HttpErrorResponse) => {
        this.inflight = null;
        if (quiet) return;
        this.pending.set(false);
        this.push({ kind: 'error', ...describe(e) });
      },
    });
  }

  private push(m: NewMsg): void {
    this.messages.update((ms) => [...ms, { ...m, id: ++this.seq } as Msg]);
  }
}

function describe(e: HttpErrorResponse): { stage: Stage; message: string } {
  if (e.status === 0) return { stage: 'network', message: 'The analytics service cannot be reached. Is the API running?' };
  const detail = e.error?.detail;
  if (detail && typeof detail === 'object' && 'stage' in detail) return { stage: detail.stage, message: detail.message };
  if (e.status === 422) return { stage: 'model', message: 'Ask a question of 3 to 500 characters.' };
  return { stage: 'model', message: `The analyst could not answer (error ${e.status}). Try again in a moment.` };
}
