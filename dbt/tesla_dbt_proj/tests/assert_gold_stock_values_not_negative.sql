-- Fails if any gold-layer aggregated stock value is negative (below 0).
-- Checks gold_stock_monthly_summary.

select *
from {{ ref('gold_stock_monthly_summary') }}
where
    month_low < 0
    or month_high < 0
    or avg_close_price < 0
    or total_volume < 0
    or total_dividends < 0
