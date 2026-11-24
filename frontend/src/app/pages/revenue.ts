import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { api, fmt, sum } from '../api';
import { LineChart, Series } from '../charts/line-chart';
import { Outcome, Outcomes } from '../charts/outcomes';
import { Asks } from '../ui/asks';
import { Change } from '../ui/change';
import { Icon } from '../ui/icon';
import { Readout } from '../ui/readout';
import { Segment, Segmented } from '../ui/segmented';
import { Trust } from '../ui/trust';

const RANGES: Segment[] = [{ id: '12', label: '1Y' }, { id: '24', label: '2Y' }, { id: '48', label: 'All' }];
const BREAKDOWNS: Segment[] = [
  { id: 'event_type', label: 'Event type' }, { id: 'service', label: 'Service' },
  { id: 'region', label: 'Region' }, { id: 'governorate', label: 'Governorate' },
];

@Component({
  selector: 'ez-revenue',
  imports: [LineChart, Outcomes, Asks, Change, Icon, Readout, Segmented, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './revenue.html',
})
export class Revenue {
  protected readonly ranges = RANGES;
  protected readonly breakdowns = BREAKDOWNS;
  protected readonly range = signal('48');
  protected readonly withForecast = signal(true);
  protected readonly breakdown = signal('event_type');
  protected readonly hover = signal<number | null>(null);

  private readonly monthly = api.revenueMonthly();
  private readonly models = api.models();
  protected readonly by = api.revenueBy(() => this.breakdown());
  protected readonly forecast = computed(() => this.models.value()?.forecast_revenue ?? null);

  protected readonly chart = computed(() => {
    const m = this.monthly.value();
    if (!m) return null;
    const shown = m.slice(-Number(this.range()));
    const f = this.withForecast() ? this.forecast()?.forecast ?? [] : [];
    const labels = [...shown.map((x) => x.month), ...f.map((x) => x.month)];
    const actual = [...shown.map((x) => x.revenue), ...f.map(() => null)];
    const series: Series[] = [{ name: 'Confirmed revenue', values: actual, fill: true }];
    if (f.length) {
      series.push({ name: 'Forecast', dashed: true, color: 'var(--series-2)',
        values: [...shown.map((_, i) => (i === shown.length - 1 ? shown[i].revenue : null)), ...f.map((x) => x.revenue)] });
    }
    return { labels, series, actualCount: shown.length, all: m };
  });

  /** the headline follows the crosshair: the hovered month against the same month a year before */
  protected readonly headline = computed(() => {
    const c = this.chart();
    if (!c) return null;
    const h = this.hover();
    const year = (y: string) => sum(c.all.filter((x) => x.month.startsWith(y)).map((x) => x.revenue));
    if (h === null) return { label: 'Confirmed revenue, 2025', value: year('2025'), change: (year('2025') / year('2024') - 1) * 100, against: 'vs 2024', forecast: false };
    const month = c.labels[h];
    const isForecast = h >= c.actualCount;
    const value = isForecast ? this.forecast()!.forecast.find((x) => x.month === month)!.revenue : c.all.find((x) => x.month === month)!.revenue;
    const prior = c.all.find((x) => x.month === `${Number(month.slice(0, 4)) - 1}${month.slice(4)}`)?.revenue;
    return { label: `${isForecast ? 'Forecast' : 'Confirmed revenue'}, ${fmt.month(month)}`, value, forecast: isForecast,
      change: prior ? (value / prior - 1) * 100 : null, against: `vs ${fmt.month(`${Number(month.slice(0, 4)) - 1}${month.slice(4)}`)}` };
  });

  protected readonly outcomes = computed<Outcome[]>(() => {
    const rows = this.by.value() ?? [];
    const top = Math.max(...rows.map((r) => r.share_pct), 1);
    const geo = this.breakdown() === 'region' || this.breakdown() === 'governorate';
    return rows.map((r, i) => ({
      label: r.label, value: fmt.compact(r.revenue), aside: fmt.pct(r.share_pct), bar: r.share_pct / top, tone: i === 0 ? 'data' : 'muted',
      sub: geo ? `${fmt.whole(r.revenue_per_1000_inhabitants)} per 1,000 inhabitants${r.region ? ' · ' + r.region : ''}` : `${fmt.whole(r.reservations)} reservations`,
    }));
  });

  protected readonly isGeo = computed(() => this.breakdown() === 'region' || this.breakdown() === 'governorate');
  protected readonly chosen = computed(() => {
    const f = this.forecast();
    return f?.holdout_results.find((r) => r.model === f.chosen_model) ?? null;
  });
  protected readonly best = computed(() => this.forecast()?.holdout_results[0] ?? null);

  protected readonly compact = (n: number) => fmt.compact(n);
  protected readonly month = (s: string) => fmt.month(s);
}
