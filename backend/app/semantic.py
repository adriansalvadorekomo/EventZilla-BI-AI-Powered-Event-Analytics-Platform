"""What the analyst model is told about the warehouse: tables, grains, columns and business definitions."""

SEMANTIC_LAYER = """
Warehouse: PostgreSQL. Only these schemas exist for you: marts, reporting, reference, quality.

STAR SCHEMA (marts)
- marts.fact_reservation: one row per reservation (18,000; 2022-2025).
  reservation_id, event_id, service_id, provider_id, beneficiary_id, governorate_id,
  reservation_date (date), event_date (date), status ('confirmed' | 'pending' | 'cancelled'),
  is_confirmed (bool), is_cancelled (bool), final_price (numeric), list_price (numeric),
  revenue (numeric: final_price of confirmed reservations, 0 otherwise),
  rating_avg (numeric 1-5, null when not evaluated), evaluations (int).
  lead_time_days exists but is unreliable (half the reservations are dated after their event): never use it.
- marts.dim_date: date_day (date), year, quarter, month, year_month ('2024-03'), weekday, is_weekend,
  season ('Spring' | 'Summer' | 'Autumn' | 'Winter'), holiday_name, is_holiday, is_ramadan.
  Join on fact_reservation.reservation_date = dim_date.date_day (or event_date).
- marts.dim_event: event_id, event_title, event_type ('Birthday' | 'Corporate Event' | 'Private Party' | 'Wedding'),
  event_date, budget, beneficiary_id.
- marts.dim_service: service_id, service_title, list_price, provider_id,
  service_category ('Venue' | 'Catering' | 'Entertainment' | 'Decoration').
- marts.dim_provider: provider_id, provider_name, service_type, city, governorate_id, complaints, complaints_open.
- marts.dim_beneficiary: beneficiary_id (a customer), email_domain, events, first_event_date, is_returning (2+ events),
  complaints.
- marts.dim_geography: governorate_id, governorate, region ('North East' | 'North West' | 'Centre East' |
  'Centre West' | 'South East' | 'South West'), population_2024, area_km2, density_per_km2.

OTHER GRAINS (reporting)
- reporting.rpt_marketing_monthly: month_start (date, 2023-01 to 2024-12), spend_type ('cheap' | 'normal' |
  'expensive'), marketing_spend, new_beneficiaries, cost_per_new_beneficiary, confirmed_revenue,
  confirmed_reservations, revenue_per_spend.
- reporting.rpt_site_traffic_daily: traffic_date (2022 only), visitors, reservations, is_valid,
  conversion_rate (null when not valid).
- reporting.rpt_complaint_summary: provider_id, subject, status ('open' | 'closed'), complaints.

QUALITY (rows excluded or flagged): quality.rejected_evaluations, quality.rejected_marketing_months,
quality.flagged_reservation_dates, quality.flagged_traffic_days.

DEFINITIONS
- Revenue = sum(revenue). Confirmation rate = avg(is_confirmed::int). Average rating = avg(rating_avg).
- Returning customers = share of dim_beneficiary with events > 0 that have is_returning.
- Complaints per 100 reservations by region: complaints from rpt_complaint_summary joined to dim_provider and
  dim_geography, divided by reservations of fact_reservation in that region.
- Revenue per inhabitant: population is a property of a governorate, not of a reservation. Aggregate revenue
  first, then divide by the population of the group taken from dim_geography alone, for example
  join (select region, sum(population_2024) as pop from marts.dim_geography group by 1) p using (region)
  and max(p.pop). Never sum population_2024 over fact rows. Express it per 1,000 inhabitants.
  Across governorates revenue does not follow population (correlation -0.01): a high figure per inhabitant
  mostly means a small population. When you report it, say so.
- Amounts have no documented currency: never add a currency symbol or name.
- The data is synthetic: differences between groups are usually small and not significant.
"""
