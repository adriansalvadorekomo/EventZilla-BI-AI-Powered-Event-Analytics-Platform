import { httpResource } from '@angular/common/http';

/** Everything the app shows comes from the analytics API (backend/), same definitions as Metabase. */

export interface Overview {
  revenue: number;
  reservations: number;
  confirmation_rate: number;
  average_rating: number;
  growth_2025_vs_2024: number;
  returning_customers: number;
  open_complaints: number;
}
export interface MonthRevenue { month: string; revenue: number; confirmed: number; }
export interface Breakdown {
  label: string;
  region?: string;
  revenue: number;
  reservations: number;
  share_pct: number;
  revenue_per_1000_inhabitants?: number;
}
export interface QuarterStatus { quarter: string; confirmed: number; pending: number; cancelled: number; }
export interface CalendarDays { days: string; revenue_per_day: number; n_days: number; }
export interface WeekConversion { week: string; conversion: number; }
export interface Customers {
  rating: { average: number; rated_4_or_more: number; evaluated: number };
  rating_quarterly: { quarter: string; rating: number; rated_4_or_more: number; evaluated: number }[];
  by_service: { label: string; rating: number }[];
  complaints_by_region: { label: string; per_100_reservations: number }[];
  complaints_by_subject: { label: string; open: number; closed: number }[];
}
export interface Marketing {
  monthly: { month: string; marketing_spend: number; new_beneficiaries: number; confirmed_revenue: number }[];
  by_type: { label: string; cost_per_new_customer: number }[];
}
export interface Freshness {
  built_at: string | null;
  gate: { passed: boolean; checks_passed: number; checks: number; run_at: string } | null;
}
export interface QualityRule { rule: string; rows: number; of_rows: number; handling: string; }
export interface ForecastReport {
  chosen_model: string;
  gate: string;
  conclusion: string;
  holdout_results: { model: string; smape: number; mase: number; passes_gate: boolean }[];
  forecast: { month: string; revenue: number }[];
}
export interface ConfirmationReport {
  passes_gate: boolean;
  conclusion: string;
  results: { gradient_boosting_auc_mean: number; dummy_auc_mean: number };
}
export interface SegmentReport {
  passes_gate: boolean;
  silhouette: number;
  segments: { name: string; action: string; customers: number; share: number }[];
}
export interface Models {
  forecast_revenue?: ForecastReport;
  predict_confirmation?: ConfirmationReport;
  segment_customers?: SegmentReport;
}
export interface SuggestedQuestion {
  id: number;
  objective: 'revenue' | 'reservations' | 'customers' | 'marketing' | 'quality';
  question: string;
  value: string | null;
  decision: string;
}
export interface Answer {
  question: string;
  answer: string;
  sql: string | null;
  columns: string[];
  rows: (string | number | null)[][];
  chart: { type: 'line' | 'bar' | 'number' | 'table'; x?: string; y?: string } | null;
  title: string | null;
  screen_risk: number;
  repaired?: boolean;
  elapsed_ms: number;
}

export const api = {
  overview: () => httpResource<Overview>(() => '/api/overview'),
  revenueMonthly: () => httpResource<MonthRevenue[]>(() => '/api/revenue/monthly'),
  revenueBy: (dimension: () => string) => httpResource<Breakdown[]>(() => `/api/revenue/by/${dimension()}`),
  status: () => httpResource<QuarterStatus[]>(() => '/api/reservations/status'),
  calendar: () => httpResource<CalendarDays[]>(() => '/api/reservations/calendar'),
  conversion: () => httpResource<WeekConversion[]>(() => '/api/conversion/weekly'),
  customers: () => httpResource<Customers>(() => '/api/customers'),
  marketing: () => httpResource<Marketing>(() => '/api/marketing'),
  quality: () => httpResource<QualityRule[]>(() => '/api/quality'),
  freshness: () => httpResource<Freshness>(() => '/api/status'),
  models: () => httpResource<Models>(() => '/api/models'),
};

const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 2 });
const whole = new Intl.NumberFormat('en', { maximumFractionDigits: 0 });

/** Amounts have no documented currency: figures only, never a symbol. */
export const fmt = {
  compact: (n: number | null | undefined) => (n == null ? '–' : compact.format(n)),
  whole: (n: number | null | undefined) => (n == null ? '–' : whole.format(n)),
  pct: (n: number | null | undefined, digits = 1) => (n == null ? '–' : `${n.toFixed(digits)}\u00a0%`),
  signedPct: (n: number) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n).toFixed(1)}\u00a0%`,
  signedPts: (n: number) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n).toFixed(1)}\u00a0pts`,
  rating: (n: number | null | undefined) => (n == null ? '–' : n.toFixed(2)),
  signedAbs: (n: number, digits = 2) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n).toFixed(digits)}`,
  stamp: (iso: string) => new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }),
  month: (ym: string) => {
    const [y, m] = ym.split('-').map(Number);
    return new Date(Date.UTC(y, m - 1, 1)).toLocaleString('en', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  },
};

/** Mean of a numeric slice. */
export const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
export const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
/** Mean of values weighted by their counts. */
export const weighted = (xs: { v: number; n: number }[]) => sum(xs.map((x) => x.v * x.n)) / (sum(xs.map((x) => x.n)) || 1);
