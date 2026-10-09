-- ============================================================
-- Live checks for the real-time sales feed.
-- Run these in pgAdmin while the producer and consumer are running,
-- and run them again to watch the numbers grow.
-- ============================================================

-- 1. How much has arrived so far
SELECT COUNT(*) AS events_loaded, SUM(total_amount) AS revenue
FROM factsalesrealtime;

-- 2. The 10 newest sales
SELECT rt_sales_key, event_time, product_category, quantity, total_amount,
       ROUND(EXTRACT(EPOCH FROM (ingested_at - event_time)) * 1000) AS latency_ms
FROM factsalesrealtime
ORDER BY rt_sales_key DESC
LIMIT 10;

-- 3. Revenue by category in the last 5 minutes
SELECT product_category, COUNT(*) AS sales, SUM(total_amount) AS revenue
FROM factsalesrealtime
WHERE ingested_at > localtimestamp - INTERVAL '5 minutes'
GROUP BY product_category
ORDER BY revenue DESC;

-- 4. Throughput: events per minute
SELECT date_trunc('minute', ingested_at) AS minute, COUNT(*) AS events
FROM factsalesrealtime
GROUP BY 1
ORDER BY 1 DESC
LIMIT 10;

-- 5. Delay between the sale and the warehouse (milliseconds)
SELECT COUNT(*) AS events,
       ROUND(AVG(EXTRACT(EPOCH FROM (ingested_at - event_time)) * 1000)) AS avg_latency_ms,
       ROUND(MAX(EXTRACT(EPOCH FROM (ingested_at - event_time)) * 1000)) AS max_latency_ms
FROM factsalesrealtime;

-- 6. Health of the queue: events loaded, rejected or still waiting
SELECT status, COUNT(*) AS events
FROM sales_event_queue
GROUP BY status
ORDER BY status;

-- 7. Why events were rejected (data quality in the stream)
SELECT id, error, payload ->> 'quantity' AS quantity, payload ->> 'product_category' AS category
FROM sales_event_queue
WHERE status = 'REJECTED'
ORDER BY id DESC
LIMIT 10;

-- 8. Batch and real-time sales together
SELECT source, COUNT(*) AS sales, SUM(total_amount) AS revenue
FROM vw_sales_batch_and_realtime
GROUP BY source;
