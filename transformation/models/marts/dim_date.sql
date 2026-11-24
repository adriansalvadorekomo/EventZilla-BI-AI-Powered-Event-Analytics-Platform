-- One row per day of the period the data covers: calendar, season (source workbook) and Tunisian holidays
-- (scraped, see ingestion/scrape_enrichment.py). Ramadan runs from its first day to the eve of Eid al-Fitr.
with days as (
  select d::date as day from generate_series('2022-01-01'::date, '2025-12-31'::date, interval '1 day') d
), holidays as (
  select day, string_agg(holiday, ' · ' order by holiday) as holiday_name, bool_or(kind = 'national') as national
  from {{ ref('stg_tn_holiday') }} group by 1
), ramadan as (
  select r.day as starts, min(e.day) - 1 as ends
  from {{ ref('stg_tn_holiday') }} r
  join {{ ref('stg_tn_holiday') }} e on e.holiday = 'Eid al-Fitr' and e.day > r.day
  where r.holiday = 'Ramadan begins'
  group by 1
)
select
  days.day                                    as date_day,
  extract(year from days.day)::int            as year,
  extract(quarter from days.day)::int         as quarter,
  extract(month from days.day)::int           as month,
  to_char(days.day, 'YYYY-MM')                as year_month,
  to_char(days.day, 'Dy')                     as weekday,
  extract(isodow from days.day) in (6, 7)     as is_weekend,
  case s.season_fr when 'Printemps' then 'Spring' when 'Été' then 'Summer'
                   when 'Automne' then 'Autumn' when 'Hiver' then 'Winter' end as season,
  h.holiday_name,
  h.holiday_name is not null                  as is_holiday,
  exists (select 1 from ramadan where days.day between ramadan.starts and ramadan.ends) as is_ramadan
from days
left join {{ ref('stg_season') }} s on s.day = days.day
left join holidays h on h.day = days.day
