{{
    config(
        materialized='table'
    )
}}

with stock as (
    select * from {{ ref('silver_stock_data') }}
),

monthly as (
    select
        date_trunc('month', trade_date)::date        as month,
        min(low_price)                               as month_low,
        max(high_price)                              as month_high,
        avg(close_price)                             as avg_close_price,
        sum(volume)                                  as total_volume,
        sum(dividend_amount)                         as total_dividends,
        count(*)                                     as trading_days,
        bool_or(dividend_amount > 0)	             as had_dividend
    from stock
    group by date_trunc('month', trade_date)
)

select * from monthly
order by month desc
