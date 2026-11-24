-- Reference only: the source has no key from events or reservations to a venue, so this table joins nothing.
select postal_code, venue, city, country from {{ ref('stg_location') }}
