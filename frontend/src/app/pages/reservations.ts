import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { api, fmt, mean } from '../api';
import { LineChart, Series } from '../charts/line-chart';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Asks } from '../ui/asks';
import { Change } from '../ui/change';
import { Icon } from '../ui/icon';
import { Readout } from '../ui/readout';
import { Trust } from '../ui/trust';

@Component({
  selector: 'ez-reservations',
  imports: [LineChart, Outcomes, Asks, Change, Icon, Readout, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './reservations.html',
})
export class Reservations {
  private readonly status = api.status();
  private readonly calendar = api.calendar();
  private readonly conversion = api.conversion();
  private readonly models = api.models();
  protected readonly hover = signal<number | null>(null);
  protected readonly convHover = signal<number | null>(null);

  protected readonly chart = computed(() => {
    const s = this.status.value();
    if (!s) return null;
    const series: Series[] = [
      { name: 'Confirmed', values: s.map((q) => q.confirmed) },
      { name: 'Pending', values: s.map((q) => q.pending), color: 'var(--series-2)' },
      { name: 'Cancelled', values: s.map((q) => q.cancelled), color: 'var(--series-2)', dashed: true },
    ];
    return { labels: s.map((q) => q.quarter), series, rows: s };
  });

  protected readonly headline = computed(() => {
    const c = this.chart();
    if (!c) return null;
    const h = this.hover();
    const last = mean(c.rows.slice(-4).map((q) => q.confirmed));
    const prev = mean(c.rows.slice(-8, -4).map((q) => q.confirmed));
    if (h === null) return { label: 'Confirmed, last four quarters', value: last, change: last - prev, against: 'vs the four quarters before' };
    const prior = c.rows[h - 4];
    return { label: `Confirmed, ${c.labels[h]}`, value: c.rows[h].confirmed,
      change: prior ? c.rows[h].confirmed - prior.confirmed : null, against: prior ? `vs ${prior.quarter}` : '' };
  });

  protected readonly days = computed<Outcome[]>(() => {
    const d = this.calendar.value() ?? [];
    const top = Math.max(...d.map((x) => x.revenue_per_day), 1);
    return d.map((x) => ({ label: x.days, value: fmt.compact(x.revenue_per_day), aside: 'per day', bar: x.revenue_per_day / top,
      sub: `${fmt.whole(x.n_days)} days`, tone: x.days === 'Other days' ? 'data' : 'muted' }));
  });

  protected readonly conv = computed(() => {
    const w = this.conversion.value();
    if (!w) return null;
    return { labels: w.map((x) => x.week), values: w.map((x) => x.conversion) };
  });

  protected readonly model = computed(() => this.models.value()?.predict_confirmation ?? null);
  protected readonly pct = (n: number) => fmt.pct(n);
  protected readonly pct2 = (n: number) => fmt.pct(n, 2);
  protected readonly week = (s: string) =>
    new Date(`${s}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
}
