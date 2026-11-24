-- Completeness, the v1 failure: every reservation of the source reaches the fact table.
select (select count(*) from {{ source('raw', 'reservation') }}) as source_rows,
       (select count(*) from {{ ref('fact_reservation') }})       as fact_rows
where (select count(*) from {{ source('raw', 'reservation') }}) <> (select count(*) from {{ ref('fact_reservation') }})
