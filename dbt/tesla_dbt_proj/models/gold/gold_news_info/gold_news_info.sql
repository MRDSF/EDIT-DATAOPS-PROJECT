{{
    config(
        materialized='table'
    )
}}

with news as (
    select * from {{ ref('silver_news') }}
)

select
    published_date,
    title,
    link,
    source
from news
