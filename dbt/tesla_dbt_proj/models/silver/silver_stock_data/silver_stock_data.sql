{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('bronze', 'bronze_stock_data') }}
),

typed as (
    select
        cast(date as date)                      as trade_date,
        cast(open as numeric(18,2))             as open_price,
        cast(high as numeric(18,2))             as high_price,
        cast(low as numeric(18,2))              as low_price,
        cast(close as numeric(18,2))            as close_price,
        cast(adjusted_close as numeric(18,2))   as adjusted_close_price,
        cast(volume as bigint)                  as volume,
        cast(dividend_amount as numeric(18,2))  as dividend_amount,
        ingested_at,
        row_number() over (
            partition by cast(date as date)
            order by ingested_at desc
        ) as rn
    from source
    where date is not null
),

deduped as (
    select * from typed where rn = 1
)

select
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    adjusted_close_price,
    volume,
    dividend_amount,
    ingested_at
from deduped
