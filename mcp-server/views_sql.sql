-- views_sql.sql

-- Drop existing views if they exist
DROP VIEW IF EXISTS customer_avg_age_by_article_group CASCADE;
DROP VIEW IF EXISTS monthly_sales_trends CASCADE;
DROP VIEW IF EXISTS top_selling_products CASCADE;

-- Customer average age by article group view (Top 1000 by revenue)
CREATE VIEW customer_avg_age_by_article_group AS
SELECT 
    a.product_group_name,
    AVG(c.age) as avg_customer_age,
    COUNT(DISTINCT c.customer_id) as total_customers,
    COUNT(*) as total_transactions,
    SUM(t.price) as total_revenue
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN articles a ON t.article_id = a.article_id
WHERE c.age IS NOT NULL
GROUP BY a.product_group_name
ORDER BY total_revenue DESC
LIMIT 1000;

-- Monthly sales trends view (unchanged)
CREATE VIEW monthly_sales_trends AS
SELECT 
    DATE_TRUNC('month', transaction_date) as month,
    COUNT(*) as transaction_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(price) as total_revenue,
    AVG(price) as avg_order_value
FROM transactions
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month;

-- Top selling products view (Top 1000 by revenue)
CREATE VIEW top_selling_products AS
SELECT 
    a.article_id,
    a.prod_name,
    a.product_group_name,
    COUNT(*) as purchase_count,
    SUM(t.price) as total_revenue,
    AVG(t.price) as avg_price
FROM transactions t
JOIN articles a ON t.article_id = a.article_id
GROUP BY a.article_id, a.prod_name, a.product_group_name
ORDER BY total_revenue DESC
LIMIT 1000;
