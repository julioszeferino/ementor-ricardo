{#
    Usa o +schema configurado (staging, marts, ...) sem o prefixo padrão do dbt
    (que geraria public_staging, public_marts, ...).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
