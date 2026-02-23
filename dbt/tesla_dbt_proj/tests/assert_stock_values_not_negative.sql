-- Fails if any stock value is negative (below 0).
-- Checks silver_stock_data prices, volume, and dividend_amount.

select *
from {{ ref('silver_stock_data') }}
where
    open_price < 0
    or high_price < 0
    or low_price < 0
    or close_price < 0
    or adjusted_close_price < 0
    or volume < 0
    or dividend_amount < 0
