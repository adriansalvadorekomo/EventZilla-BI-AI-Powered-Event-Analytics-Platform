import { ChangeDetectionStrategy, Component, computed, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { api, fmt, mean, sum, weighted } from '../api';
import { LineChart } from '../charts/line-chart';
import { Change } from '../ui/change';
import { Icon } from '../ui/icon';
import { Readout } from '../ui/readout';
import { Trust } from '../ui/trust';

/** The market board: every objective as a market tile, and what the quality rules did before these figures. */
@Component({
  selector: 'ez-board',
  imports: [RouterLink, LineChart, Change, Icon, Readout, Trust],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './board.html',
  styleUrl: './board.css',
})
export class Board {
  private readonly monthly = api.revenueMonthly();
  private readonly status = api.status();
  private readonly customers = api.customers();
  private readonly marketing = api.marketing();
  protected readonly quality = api.quality();
  protected readonly fresh = api.freshness();
  protected readonly fmt = fmt;
  /** one crosshair per tile: the reading appears in the chart, the headline stays put */
  protected readonly hRev = signal<number | null>(null);
  protected readonly hRes = signal<number | null>(null);
  protected readonly hCus = signal<number | null>(null);
  protected readonly hMkt = signal<number | null>(null);
  protected readonly failed = computed(() =>
    [this.monthly, this.status, this.customers, this.marketing].some((r) => r.error()));

  protected readonly revenue = computed(() => {
    const m = this.monthly.value();
    if (!m) return null;
    const year = (y: string) => sum(m.filter((x) => x.month.startsWith(y)).map((x) => x.revenue));
    const y25 = year('2025');
    return { total: y25, change: (y25 / year('2024') - 1) * 100, labels: m.map((x) => x.month), values: m.map((x) => x.revenue) };
  });

  protected readonly reservations = computed(() => {
    const s = this.status.value();
    if (!s) return null;
    const last = mean(s.slice(-4).map((q) => q.confirmed));
    const prev = mean(s.slice(-8, -4).map((q) => q.confirmed));
    return { rate: last, change: last - prev, labels: s.map((q) => q.quarter), values: s.map((q) => q.confirmed) };
  });

  protected readonly satisfaction = computed(() => {
    const c = this.customers.value();
    if (!c) return null;
    const q = c.rating_quarterly;
    const avg = (rows: typeof q) => weighted(rows.map((x) => ({ v: x.rating, n: x.evaluated })));
    const last = avg(q.slice(-4));
    return { rating: last, change: last - avg(q.slice(-8, -4)), labels: q.map((x) => x.quarter), values: q.map((x) => x.rating) };
  });

  protected readonly acquisition = computed(() => {
    const k = this.marketing.value();
    if (!k) return null;
    const m = k.monthly;
    const cost = (y: string) => {
      const rows = m.filter((x) => x.month.startsWith(y));
      return sum(rows.map((x) => x.marketing_spend)) / sum(rows.map((x) => x.new_beneficiaries));
    };
    const all = sum(m.map((x) => x.marketing_spend)) / sum(m.map((x) => x.new_beneficiaries));
    return { cost: all, change: (cost('2024') / cost('2023') - 1) * 100,
      labels: m.map((x) => x.month), values: m.map((x) => x.marketing_spend / x.new_beneficiaries) };
  });

  protected readonly rules = computed(() => this.quality.value()?.map((r) => ({ ...r, share: (100 * r.rows) / r.of_rows })) ?? []);

  protected readonly pct = (n: number) => fmt.pct(n);
  protected readonly rating = (n: number) => n.toFixed(2);
  protected readonly compact = (n: number) => fmt.compact(n);
  protected readonly whole = (n: number) => fmt.whole(n);
  protected readonly month = (s: string) => fmt.month(s);
  protected readonly cost = (n: number) => n.toFixed(1);
  protected readonly stamp = (s: string) => fmt.stamp(s);
  protected readonly quarter = (s: string) => s.replace('-', ' ');
}
