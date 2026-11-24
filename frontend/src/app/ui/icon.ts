import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/** Authored icons: 24-unit grid, 1.75 stroke, round caps. One family for the whole app. */
const PATHS: Record<string, string> = {
  up: 'M7 17 17 7M9 7h8v8',
  down: 'M7 7l10 10M17 9v8H9',
  flat: 'M5 12h14',
  right: 'M5 12h14M13 6l6 6-6 6',
  send: 'M5 12h13M12 5l7 7-7 7',
  close: 'M6 6l12 12M18 6 6 18',
  ask: 'M4 5h16v11H9l-5 4z M8 9.5h8 M8 12.5h5',
  check: 'M5 12.5l4.5 4.5L19 7',
  gate: 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z M9 12l2 2 4-4',
  stop: 'M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z M9.5 9.5l5 5M14.5 9.5l-5 5',
  chevron: 'M6 9l6 6 6-6',
  list: 'M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 11v6 M12 7.5h.01',
};

@Component({
  selector: 'ez-icon',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<svg viewBox="0 0 24 24" [attr.width]="size()" [attr.height]="size()" aria-hidden="true"
    fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path [attr.d]="d()" /></svg>`,
  styles: `:host { display: inline-flex; flex: none; } svg { display: block; }`,
})
export class Icon {
  readonly name = input.required<string>();
  readonly size = input(16);
  protected d = () => PATHS[this.name()] ?? '';
}
