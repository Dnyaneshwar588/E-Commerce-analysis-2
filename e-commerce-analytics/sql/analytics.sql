-- Amazon Sales Analytics SQL Pack
-- Run these queries against a table named amazon_sales.

-- 1. Total revenue and order volume
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value
FROM amazon_sales;

-- 2. Monthly sales trend
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(amount) AS revenue,
    COUNT(*) AS orders
FROM amazon_sales
GROUP BY month
ORDER BY month;

-- 3. Category-wise sales
SELECT
    category,
    SUM(amount) AS revenue,
    SUM(qty) AS quantity
FROM amazon_sales
GROUP BY category
ORDER BY revenue DESC;

-- 4. Top-selling products
SELECT
    style,
    sku,
    SUM(amount) AS revenue,
    SUM(qty) AS quantity,
    COUNT(*) AS orders
FROM amazon_sales
GROUP BY style, sku
ORDER BY revenue DESC
LIMIT 10;

-- 5. State-wise sales
SELECT
    ship_state,
    COUNT(*) AS orders,
    SUM(amount) AS revenue
FROM amazon_sales
GROUP BY ship_state
ORDER BY revenue DESC;

-- 6. B2B vs Non-B2B
SELECT
    CASE WHEN b2b = 1 THEN 'B2B' ELSE 'Non-B2B' END AS segment,
    COUNT(*) AS orders,
    SUM(amount) AS revenue
FROM amazon_sales
GROUP BY segment;
