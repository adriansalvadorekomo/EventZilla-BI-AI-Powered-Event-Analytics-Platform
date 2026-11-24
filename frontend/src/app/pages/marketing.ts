import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { api, fmt, sum } from '../api';
import { LineChart } from '../charts/line-chart';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Asks } from '../ui/asks';
import { Change } from '../ui/change';
import { Readout } from '../ui/readout';
import { Trust } from '../ui/trust';

@Component({
  selector: 'ez-marketing',
  imports: [LineChart, Outcomes, Asks, Change, Readout, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './marketing.html',
  styles: `.stack { display: grid; gap: 0.25rem; } .stack .chart-well { padding-top: 0.75rem; }`,
})
export class Marketing {
  private readonly data = api.marketing();
  /** one crosshair for the three charts: they share the months */
  protected readonly hover = signal<number | null>(null);

  protected readonly m = computed(() => this.data.value()?.monthly ?? null);
  protected readonly labels = computed(() => this.m()?.map((x) => x.month) ?? []);
  protected readonly spend = computed(() => [{ name: 'Marketing spend', values: this.m()?.map((x) => x.marketing_spend) ?? [], color: 'var(--series-2)' }]);
  protected readonly customers = computed(() => [{ name: 'New customers', values: this.m()?.map((x) => x.new_beneficiaries) ?? [], fill: true }]);
  protected readonly revenue = computed(() => [{ name: 'Confirmed revenue', values: this.m()?.map((x) => x.confirmed_revenue) ?? [] }]);

  protected readonly headline = computed(() => {
    const m = this.m();
    if (!m) return null;
    const h = this.hover();
    const cost = (rows: typeof m) => sum(rows.map((x) => x.marketing_spend)) / sum(rows.map((x) => x.new_beneficiaries));
    if (h === null) {
      return { label: 'Spend per new customer, 2023–2024', value: cost(m),
        change: (cost(m.filter((x) => x.month.startsWith('2024'))) / cost(m.filter((x) => x.month.startsWith('2023'))) - 1) * 100, against: '2024 vs 2023' };
    }
    const prior = m.find((x) => x.month === `${Number(m[h].month.slice(0, 4)) - 1}${m[h].month.slice(4)}`);
    return { label: `Spend per new customer, ${fmt.month(m[h].month)}`, value: cost([m[h]]),
      change: prior ? (cost([m[h]]) / cost([prior]) - 1) * 100 : null, against: prior ? `vs ${fmt.month(prior.month)}` : '' };
  });

  protected readonly types = computed<Outcome[]>(() => {
    const t = this.data.value()?.by_type ?? [];
    const top = Math.max(...t.map((x) => x.cost_per_new_customer), 1);
    return t.map((x, i) => ({ label: `${x.label[0].toUpperCase()}${x.label.slice(1)} months`, value: x.cost_per_new_customer.toFixed(1),
      aside: 'per new customer', bar: x.cost_per_new_customer / top, tone: i === 0 ? 'data' : 'muted' }));
  });

  protected readonly cost = (n: number) => n.toFixed(1);
  protected readonly compact = (n: number) => fmt.compact(n);
  protected readonly whole = (n: number) => fmt.whole(n);
  protected readonly month = (s: string) => fmt.month(s);
}
