{# Accent- and case-insensitive key for governorate names ('Kébili' = 'Kebili'). #}
{% macro geo_key(col) -%}
  lower(translate({{ col }}, 'ÀÂÄÉÈÊËÎÏÔÖÙÛÜÇàâäéèêëîïôöùûüç', 'AAAEEEEIIOOUUUCaaaeeeeiioouuuc'))
{%- endmacro %}
