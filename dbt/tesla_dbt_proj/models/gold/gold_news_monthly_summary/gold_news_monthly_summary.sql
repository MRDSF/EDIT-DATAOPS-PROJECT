{{
    config(
        materialized='table'
    )
}}

with news as (
    select * from {{ ref('silver_news') }}
),

aggregated as (
    select
        source,
        date_trunc('month', published_date)::date   as month,
        count(*)                                    as total_articles,
        count(distinct published_date)              as distinct_days_with_articles,
        round(count(*)::numeric / nullif(count(distinct published_date), 0), 2) as avg_articles_per_day
    from news
    group by source, date_trunc('month', published_date)
)

select
    source,
    month,
    total_articles,
    distinct_days_with_articles,
    avg_articles_per_day
from aggregated
order by month desc, source
