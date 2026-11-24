import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { api, fmt, weighted } from '../api';
import { LineChart } from '../charts/line-chart';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Asks } from '../ui/asks';
import { Change } from '../ui/change';
import { Readout } from '../ui/readout';
import { Trust } from '../ui/trust';

@Component({
  selector: 'ez-customers',
  imports: [LineChart, Outcomes, Asks, Change, Readout, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './customers.html',
})
export class Customers {
  private readonly data = api.customers();
  private readonly overview = api.overview();
  private readonly models = api.models();
  protected readonly hover = signal<number | null>(null);
  protected readonly o = this.overview.value;

  protected readonly chart = computed(() => {
    const c = this.data.value();
    if (!c) return null;
    const q = c.rating_quarterly;
    return { labels: q.map((x) => x.quarter), rows: q, rating: c.rating,
      series: [{ name: 'Average rating', values: q.map((x) => x.rating), fill: true }] };
  });

  protected readonly headline = computed(() => {
    const c = this.chart();
    if (!c) return null;
    const h = this.hover();
    if (h === null) {
      const avg = (rows: typeof c.rows) => weighted(rows.map((x) => ({ v: x.rating, n: x.evaluated })));
      const last = avg(c.rows.slice(-4));
      return { label: 'Average rating, last four quarters', value: last, change: last - avg(c.rows.slice(-8, -4)), against: 'vs the four quarters before' };
    }
    const prior = c.rows[h - 4];
    return { label: `Average rating, ${c.labels[h]}`, value: c.rows[h].rating,
      change: prior ? c.rows[h].rating - prior.rating : null, against: prior ? `vs ${prior.quarter}` : '' };
  });

  protected readonly segments = computed<Outcome[]>(() => {
    const s = this.models.value()?.segment_customers;
    if (!s) return [];
    return s.segments.map((x, i) => ({ label: x.name, value: fmt.pct(x.share * 100, 0), aside: `${fmt.whole(x.customers)} customers`,
      bar: x.share, sub: x.action, tone: i === 0 ? 'data' : 'muted' }));
  });
  protected readonly silhouette = computed(() => this.models.value()?.segment_customers?.silhouette ?? null);

  protected readonly services = computed<Outcome[]>(() =>
    (this.data.value()?.by_service ?? []).map((x, i) => ({ label: x.label, value: `${x.rating.toFixed(2)} / 5`, bar: (x.rating - 1) / 4, tone: i === 0 ? 'data' : 'muted' })));

  protected readonly regions = computed<Outcome[]>(() => {
    const r = this.data.value()?.complaints_by_region ?? [];
    const top = Math.max(...r.map((x) => x.per_100_reservations), 1);
    return r.map((x, i) => ({ label: x.label, value: x.per_100_reservations.toFixed(1), aside: 'per 100 reservations', bar: x.per_100_reservations / top, tone: i === 0 ? 'data' : 'muted' }));
  });

  protected readonly subjects = computed<Outcome[]>(() => {
    const s = this.data.value()?.complaints_by_subject ?? [];
    const top = Math.max(...s.map((x) => x.open + x.closed), 1);
    return s.map((x) => ({ label: x.label, value: `${fmt.whole(x.open)} open`, aside: `${fmt.whole(x.closed)} closed`, bar: x.open / top, tone: 'muted' }));
  });

  protected readonly spread = computed(() => {
    const r = this.data.value()?.complaints_by_region ?? [];
    return r.length ? Math.max(...r.map((x) => x.per_100_reservations)) - Math.min(...r.map((x) => x.per_100_reservations)) : null;
  });

  protected readonly rating = (n: number) => n.toFixed(2);
  protected readonly pct = (n: number) => fmt.pct(n);
}
