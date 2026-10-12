-- ============================================================
-- Live REST API ingestion: what we can derive from the stream
-- Run in pgAdmin on the database  realtime_demo.
-- Select ONE query at a time and press F5. Run again to see new data.
-- ============================================================

-- 1. How much has been ingested
SELECT metric, COUNT(*) AS readings,
       MIN(fetched_at) AS first_reading, MAX(fetched_at) AS last_reading
FROM live_readings
GROUP BY metric
ORDER BY metric;

-- 2. Latest value of every metric
SELECT DISTINCT ON (metric) metric, value, fetched_at
FROM live_readings
ORDER BY metric, fetched_at DESC;

-- 3. Change since the first reading (absolute and percent)
SELECT metric,
       first_value AS first_value, last_value AS latest_value,
       ROUND(last_value - first_value, 4) AS change,
       ROUND(100 * (last_value - first_value) / NULLIF(first_value, 0), 4) AS change_percent
FROM (
    SELECT DISTINCT metric,
           FIRST_VALUE(value) OVER (PARTITION BY metric ORDER BY fetched_at
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS first_value,
           LAST_VALUE(value)  OVER (PARTITION BY metric ORDER BY fetched_at
                                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_value
    FROM live_readings
) t
ORDER BY metric;

-- 4. Statistics for the last 5 minutes (low, high, average, volatility)
SELECT metric, COUNT(*) AS readings, MIN(value) AS low, MAX(value) AS high,
       ROUND(AVG(value), 4) AS average, ROUND(STDDEV_SAMP(value), 4) AS volatility
FROM live_readings
WHERE fetched_at > localtimestamp - INTERVAL '5 minutes'
GROUP BY metric
ORDER BY metric;

-- 5. One-minute candles: open, high, low, close
SELECT metric, date_trunc('minute', fetched_at) AS minute,
       (ARRAY_AGG(value ORDER BY fetched_at))[1]      AS open,
       MAX(value)                                     AS high,
       MIN(value)                                     AS low,
       (ARRAY_AGG(value ORDER BY fetched_at DESC))[1] AS close,
       COUNT(*)                                       AS readings
FROM live_readings
GROUP BY metric, date_trunc('minute', fetched_at)
ORDER BY minute DESC, metric
LIMIT 20;

-- 6. Moving average of the last 5 readings (smooths the noise)
SELECT metric, fetched_at, value,
       ROUND(AVG(value) OVER (PARTITION BY metric ORDER BY fetched_at
                              ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 4) AS moving_avg_5
FROM live_readings
ORDER BY fetched_at DESC, metric
LIMIT 20;

-- 7. Biggest jumps between two readings in a row
SELECT metric, fetched_at, value,
       ROUND(value - LAG(value) OVER (PARTITION BY metric ORDER BY fetched_at), 4) AS jump
FROM live_readings
ORDER BY ABS(value - LAG(value) OVER (PARTITION BY metric ORDER BY fetched_at)) DESC NULLS LAST
LIMIT 10;

-- 8. Health of the ingestion: API speed and problems logged
SELECT (SELECT COUNT(*) FROM live_readings)              AS readings_stored,
       (SELECT ROUND(AVG(response_ms)) FROM live_readings) AS avg_api_ms,
       (SELECT MAX(response_ms) FROM live_readings)       AS slowest_api_ms,
       (SELECT COUNT(*) FROM ingest_errors)               AS problems_logged;

-- 9. What went wrong (rejected values, network errors)
SELECT logged_at, source, problem
FROM ingest_errors
ORDER BY id DESC
LIMIT 10;
