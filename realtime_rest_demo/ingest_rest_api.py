"""
LIVE REST API INGESTION  (standalone exercise, not part of the ERP warehouse)

Calls a public REST API every few seconds, validates what comes back and stores it in
its own PostgreSQL database (realtime_demo). Nothing here touches uc15_dw.

Two public APIs are supported. Neither needs an account or a key:
  coinbase   live prices, e.g. BTC-USD and ETH-USD   (https://api.coinbase.com)
  iss        live position and speed of the International Space Station (https://api.wheretheiss.at)

Run (from this folder):
    python3 ingest_rest_api.py                          # coinbase, every 5 seconds, until Ctrl+C
    python3 ingest_rest_api.py --source iss             # use the ISS API instead
    python3 ingest_rest_api.py --interval 3 --count 20  # 20 rounds, 3 seconds apart
    python3 ingest_rest_api.py --base-url http://127.0.0.1:8099   # use mock_api_server.py (works offline)

The database and tables are created automatically on the first run.
Stop with Ctrl+C. Then run the queries in live_queries.sql in pgAdmin (database realtime_demo).
"""
import argparse
import json
import math
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import psycopg2

DB = dict(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("UC15_DB_PASSWORD", "uc15pass"),
)
DBNAME = os.getenv("RT_DATABASE", "realtime_demo")

DEFAULT_BASE = {"coinbase": "https://api.coinbase.com", "iss": "https://api.wheretheiss.at"}

DDL = """
CREATE TABLE IF NOT EXISTS live_readings (
    id          BIGSERIAL PRIMARY KEY,
    source      VARCHAR(20)   NOT NULL,
    metric      VARCHAR(40)   NOT NULL,
    value       NUMERIC(24,8) NOT NULL,
    api_time    TIMESTAMP,                 -- time given by the API, when it gives one (UTC)
    fetched_at  TIMESTAMP     NOT NULL,    -- when we received it (local time)
    response_ms INT           NOT NULL     -- how long the API took to answer
);
CREATE INDEX IF NOT EXISTS idx_live_metric_time ON live_readings (metric, fetched_at);

CREATE TABLE IF NOT EXISTS ingest_errors (
    id        BIGSERIAL PRIMARY KEY,
    source    VARCHAR(20) NOT NULL,
    problem   TEXT        NOT NULL,
    logged_at TIMESTAMP   NOT NULL
);
"""


def ensure_database():
    """Create the realtime_demo database on the first run, then return a connection to it."""
    admin = psycopg2.connect(dbname="postgres", **DB)
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DBNAME,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{DBNAME}"')
            print(f"Created database {DBNAME}")
    admin.close()
    conn = psycopg2.connect(dbname=DBNAME, **DB)
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    return conn


def http_get_json(url, timeout=8):
    """One REST call. Returns the decoded JSON and how many milliseconds the API took."""
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "realtime-demo/1.0"})
    started = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body, int((time.time() - started) * 1000)


# ---- one small adapter per API: build the URL(s), turn the JSON into (metric, value, api_time) ----
def coinbase_requests(base, symbols):
    return [(f"{base}/v2/prices/{sym}/spot", sym) for sym in symbols]


def coinbase_parse(body, sym):
    return [(sym, float(body["data"]["amount"]), None)]


def iss_requests(base, _symbols):
    return [(f"{base}/v1/satellites/25544", "iss")]


def iss_parse(body, _tag):
    when = datetime.fromtimestamp(body["timestamp"], tz=timezone.utc).replace(tzinfo=None)
    return [("iss_latitude", float(body["latitude"]), when), ("iss_longitude", float(body["longitude"]), when),
            ("iss_altitude_km", float(body["altitude"]), when), ("iss_velocity_kmh", float(body["velocity"]), when)]


ADAPTERS = {"coinbase": (coinbase_requests, coinbase_parse), "iss": (iss_requests, iss_parse)}


def check(metric, value):
    """Return a problem text when the value is not acceptable, else None."""
    if not math.isfinite(value):
        return "value is not a finite number"
    if metric.endswith("-USD") and value <= 0:
        return "price must be above zero"
    if metric == "iss_latitude" and not -90 <= value <= 90:
        return "latitude out of range"
    if metric == "iss_longitude" and not -180 <= value <= 180:
        return "longitude out of range"
    if metric in ("iss_altitude_km", "iss_velocity_kmh") and value <= 0:
        return "value must be above zero"
    return None


def log_error(conn, source, problem):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO ingest_errors (source, problem, logged_at) VALUES (%s,%s,%s)", (source, problem[:500], datetime.now()))
    conn.commit()
    print(f"[{datetime.now():%H:%M:%S}] ERROR logged, will try again: {problem[:120]}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Live REST API ingestion into PostgreSQL")
    ap.add_argument("--source", choices=sorted(ADAPTERS), default="coinbase")
    ap.add_argument("--symbols", default="BTC-USD,ETH-USD", help="coinbase only, comma separated")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between rounds (default 5)")
    ap.add_argument("--count", type=int, default=0, help="number of rounds, 0 = until Ctrl+C")
    ap.add_argument("--base-url", default=None, help="replace the API address, e.g. a local mock server")
    args = ap.parse_args()

    base = args.base_url or DEFAULT_BASE[args.source]
    build, parse = ADAPTERS[args.source]
    plan = build(base, [s.strip() for s in args.symbols.split(",") if s.strip()])
    conn = ensure_database()
    last = {}
    rounds = 0
    print(f"Source: {args.source} ({base}). One round every {args.interval}s. Press Ctrl+C to stop.", flush=True)
    try:
        while args.count == 0 or rounds < args.count:
            rounds += 1
            for url, tag in plan:
                try:
                    body, ms = http_get_json(url)
                    records = parse(body, tag)
                except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
                    log_error(conn, args.source, f"{url}: {type(exc).__name__}: {exc}")
                    continue
                for metric, value, api_time in records:
                    problem = check(metric, value)
                    if problem:
                        log_error(conn, args.source, f"{metric}={value} rejected: {problem}")
                        continue
                    with conn.cursor() as cur:
                        cur.execute("INSERT INTO live_readings (source, metric, value, api_time, fetched_at, response_ms) VALUES (%s,%s,%s,%s,%s,%s)",
                                    (args.source, metric, value, api_time, datetime.now(), ms))
                    conn.commit()
                    change = "" if metric not in last else f"  ({value - last[metric]:+.4f} vs previous)"
                    last[metric] = value
                    print(f"[{datetime.now():%H:%M:%S}] {metric:<18} {value:>16,.4f}{change}  API {ms} ms", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        print(f"Stopped after {rounds} rounds.")


if __name__ == "__main__":
    main()
