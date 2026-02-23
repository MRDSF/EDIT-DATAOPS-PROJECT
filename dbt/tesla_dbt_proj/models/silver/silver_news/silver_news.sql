{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('bronze', 'bronze_news') }}
),

cleaned as (
    select
        id,
        trim(date_raw)                          as date_raw,
        cast(trim(date_raw) as date)            as published_date,
        trim(title)                             as title,
        trim(link)                              as link,
        trim(source)                            as source,
        trim(file_name)                         as file_name,
        ingested_at,
        row_number() over (
            partition by trim(source), trim(title), trim(date_raw)
            order by ingested_at desc
        ) as rn
    from source
    where
        date_raw is not null
        and title is not null
        and link is not null
),

deduped as (
    select * from cleaned where rn = 1
)

select
    id,
    date_raw,
    published_date,
    title,
    link,
    source,
    file_name,
    ingested_at
from deduped
