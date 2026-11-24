{# Raw values arrive as text, exactly as in the workbook: empty string = missing. #}
{% macro txt(col) -%} nullif(trim(cast({{ col }} as text)), '') {%- endmacro %}
{% macro int_(col) -%} cast(cast({{ txt(col) }} as numeric) as integer) {%- endmacro %}
{% macro num(col) -%} cast(replace({{ txt(col) }}, ',', '.') as numeric) {%- endmacro %}
{# Excel dates land as "2025-05-29 00:00:00" or "2025-05-29" #}
{% macro day(col) -%} cast(left({{ txt(col) }}, 10) as date) {%- endmacro %}
