-- ============================================================
-- UC15 ERP Data Platform - ETL audit log
--
-- One table that records every run of the Pentaho job ETL_Load_Warehouse:
-- when it started, each stage it finished, how many rows each table received,
-- whether the reconciliation passed, and whether the run succeeded or failed.
--
-- It is separate from the 15 warehouse tables, so the reset script and the
-- reconciliation check do not touch it. Safe to run more than once.
-- ============================================================
CREATE TABLE IF NOT EXISTS etl_run_log (
    log_id     BIGSERIAL PRIMARY KEY,
    run_id     VARCHAR(30)  NOT NULL,                      -- same value for every row of one job run
    job_name   VARCHAR(60)  NOT NULL,
    step_name  VARCHAR(100) NOT NULL,
    status     VARCHAR(10)  NOT NULL,                      -- STARTED, SUCCESS or FAILED
    message    TEXT,
    logged_at  TIMESTAMP    NOT NULL DEFAULT localtimestamp
);

CREATE INDEX IF NOT EXISTS idx_etl_run_log_run ON etl_run_log (run_id, log_id);

-- Handy view: the latest run only
CREATE OR REPLACE VIEW vw_etl_last_run AS
SELECT * FROM etl_run_log
WHERE run_id = (SELECT run_id FROM etl_run_log ORDER BY log_id DESC LIMIT 1)
ORDER BY log_id;
