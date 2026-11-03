-- Currency is integer GBP pence. Source includes credit notes and missing customer IDs.
DROP TABLE IF EXISTS invoices;
CREATE TABLE invoices AS
SELECT invoice_no,MIN(invoice_date) invoice_date,MIN(month) month,
       CASE WHEN COUNT(DISTINCT country)=1 THEN MIN(country) ELSE 'Multiple markets' END country,
       CASE WHEN COUNT(DISTINCT NULLIF(customer_id,''))=1 THEN MAX(customer_id) ELSE '' END customer_id,
       SUM(MAX(line_cents,0)) gross_cents,SUM(MAX(-line_cents,0)) credit_cents,
       SUM(line_cents) net_cents,COUNT(*) line_count
FROM invoice_lines GROUP BY invoice_no;

DROP TABLE IF EXISTS monthly_country;
CREATE TABLE monthly_country AS
SELECT month,country,SUM(gross_cents) gross_cents,SUM(credit_cents) credit_cents,
       SUM(net_cents) net_cents,SUM(CASE WHEN gross_cents>0 THEN 1 ELSE 0 END) positive_orders,
       SUM(CASE WHEN credit_cents>0 THEN 1 ELSE 0 END) credit_invoices,SUM(line_count) line_count
FROM invoices GROUP BY month,country;

DROP TABLE IF EXISTS market_controls;
CREATE TABLE market_controls AS
SELECT country,SUM(gross_cents) gross_cents,SUM(credit_cents) credit_cents,SUM(net_cents) net_cents,
       SUM(CASE WHEN gross_cents>0 THEN 1 ELSE 0 END) positive_orders
FROM invoices GROUP BY country;

DROP TABLE IF EXISTS customer_review;
CREATE TABLE customer_review AS
WITH customer_aggregate AS (
  SELECT customer_id,
         CASE WHEN COUNT(DISTINCT country)=1 THEN MIN(country) ELSE 'Multiple markets' END country,
         CAST(julianday('2011-12-01')-julianday(MAX(CASE WHEN gross_cents>0 THEN invoice_date END)) AS INTEGER) recency_days,
         SUM(CASE WHEN gross_cents>0 THEN 1 ELSE 0 END) positive_orders,
         SUM(gross_cents) gross_cents,SUM(credit_cents) credit_cents,SUM(net_cents) net_cents
  FROM invoices WHERE customer_id<>'' GROUP BY customer_id
)
SELECT *,RANK() OVER (ORDER BY gross_cents DESC) gross_value_rank,
       SUM(gross_cents) OVER (ORDER BY gross_cents DESC,customer_id ROWS UNBOUNDED PRECEDING)*1.0
         /NULLIF(SUM(gross_cents) OVER (),0) cumulative_gross_share
FROM customer_aggregate;

DROP TABLE IF EXISTS product_review;
CREATE TABLE product_review AS
SELECT stock_code,SUM(MAX(line_cents,0)) gross_cents,SUM(MAX(-line_cents,0)) credit_cents,
       SUM(line_cents) net_cents,SUM(quantity) net_units
FROM invoice_lines GROUP BY stock_code;
