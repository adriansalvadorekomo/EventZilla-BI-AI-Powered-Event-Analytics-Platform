import { ChangeDetectionStrategy, Component, computed } from '@angular/core';
import { api, fmt } from '../api';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Asks } from '../ui/asks';
import { Icon } from '../ui/icon';
import { Trust } from '../ui/trust';

@Component({
  selector: 'ez-quality',
  imports: [Outcomes, Asks, Icon, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './quality.html',
  styles: `
    .steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 0; counter-reset: s; }
    .steps li { display: grid; grid-template-columns: 2rem 1fr; gap: 0.75rem; padding: 0.875rem 0; border-top: 1px solid var(--line); }
    .steps li:first-child { border-top: 0; }
    .steps .n { width: 2rem; height: 2rem; display: grid; place-items: center; border-radius: 50%; background: var(--display); border: 1px solid var(--line-strong); font-family: var(--mono); font-size: 0.75rem; color: var(--ink-2); }
    .steps h3 { margin-bottom: 0.125rem; }
    .steps p { color: var(--ink-3); font-size: 0.875rem; max-width: 68ch; }
    .models { display: grid; gap: 0.625rem; }
  `,
})
export class Quality {
  private readonly rules = api.quality();
  protected readonly models = api.models();

  protected readonly chosenError = computed(() => {
    const f = this.models.value()?.forecast_revenue;
    return f?.holdout_results.find((r) => r.model === f.chosen_model)?.smape ?? null;
  });

  protected readonly rows = computed<Outcome[]>(() =>
    (this.rules.value() ?? []).map((r) => ({
      label: r.rule, value: fmt.whole(r.rows), aside: `of ${fmt.whole(r.of_rows)} · ${fmt.pct((100 * r.rows) / r.of_rows)}`,
      bar: r.rows / r.of_rows, sub: r.handling, tone: r.handling.startsWith('left') || r.handling.startsWith('conversion') ? 'gate' : 'muted',
    })));
}
