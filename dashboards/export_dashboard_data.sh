#!/bin/sh
# Exports the dashboard views (sql/11_dashboard_views.sql) to CSV files in dashboards/data/.
# Run it after the warehouse has been (re)loaded, then refresh the data in Power BI.
#
#   cd ~/Data-Engineering-UC15 && sh dashboards/export_dashboard_data.sh
#
# Settings (all optional):  PSQL  = path to psql   (default: the Mac PostgreSQL 18 installer's psql)
#                           UC15_DB_PASSWORD = database password (default: uc15pass)
PSQL="${PSQL:-/Library/PostgreSQL/18/bin/psql}"
export PGPASSWORD="${UC15_DB_PASSWORD:-uc15pass}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/data"
mkdir -p "$OUT"

for v in vw_dash_sales vw_dash_procurement vw_dash_receivables vw_dash_inventory_demand vw_dash_warehouse \
         vw_dash_manufacturing vw_dash_assets vw_dash_customers vw_dash_employees vw_dash_finance vw_dash_data_checks; do
  "$PSQL" -h localhost -U postgres -d uc15_dw -q -c "\copy (SELECT * FROM $v) TO '$OUT/$v.csv' CSV HEADER" || { echo "FAILED: $v"; exit 1; }
  echo "$v.csv  $(($(wc -l < "$OUT/$v.csv") - 1)) rows"
done

# the layer reconciliation result is written by python/ERP_Layer_Reconciliation.py
if [ -f "$HERE/../silver/validation/layer_reconciliation.csv" ]; then
  cp "$HERE/../silver/validation/layer_reconciliation.csv" "$OUT/layer_reconciliation.csv"
  echo "layer_reconciliation.csv  copied"
else
  echo "Note: run python/ERP_Layer_Reconciliation.py first to get layer_reconciliation.csv"
fi
