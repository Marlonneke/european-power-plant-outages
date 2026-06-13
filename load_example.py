"""European Power Plant Outages — quick-start loader.

Three ways to load the data (pick your stack). All read the Parquet directly; no setup beyond the
library. Files: `outages_all.parquet` (everything) or the partitioned `zone=…/year=…/` tree.
"""

# ─────────────────────────── pandas ───────────────────────────
import pandas as pd

# Everything in one shot (the full file is only a few MB):
df = pd.read_parquet("outages_all.parquet")

# Common slices:
fr_nuclear_trips = df[(df.zone == "FR") & (df.fuel == "Nuclear") & (df.status == "forced")]
big_outages = df[df.mw_unavailable >= 500].sort_values("outage_start")
in_window = df[(df.outage_start >= "2024-01-01") & (df.outage_start < "2025-01-01")]

# Load ONE partition only (no full scan) — e.g. just French 2024:
fr_2024 = pd.read_parquet("outages/zone=FR/year=2024")

# The pre-aggregated daily MW-offline curve (the modelling feature):
curve = pd.read_parquet("daily_curve/")          # zone, date, fuel, mw_offline, mw_offline_forced, n_outages
fr_nuke_offline = curve[(curve.zone == "FR") & (curve.fuel == "Nuclear")].set_index("date")["mw_offline"]


# ─────────────────────────── DuckDB (SQL, lazy, no full load) ───────────────────────────
# pip install duckdb
import duckdb

con = duckdb.connect()
# Partition columns (zone, year) are recovered from the directory names automatically:
hot = con.sql("""
    SELECT zone, unit_name, fuel, outage_start, outage_end, mw_unavailable
    FROM 'outages/zone=*/year=*/*.parquet'
    WHERE status = 'forced' AND mw_unavailable > 500
    ORDER BY outage_start DESC
""").df()

# Total forced MW offline per day in France, straight from the curve:
fr = con.sql("""
    SELECT date, SUM(mw_offline_forced) AS fr_forced_mw
    FROM 'daily_curve/zone=FR/**/*.parquet'
    GROUP BY date ORDER BY date
""").df()


# ─────────────────────────── Polars ───────────────────────────
# pip install polars
import polars as pl

lf = pl.scan_parquet("outages_all.parquet")      # lazy
recent_gas = (
    lf.filter((pl.col("fuel") == "Fossil Gas") & (pl.col("status") == "forced"))
      .select(["zone", "unit_name", "outage_start", "mw_unavailable"])
      .collect()
)


if __name__ == "__main__":
    print(f"rows: {len(df):,} | zones: {sorted(df.zone.unique())} "
          f"| {df.outage_start.min()} → {df.outage_start.max()}")
    print(df[["zone", "unit_name", "fuel", "status", "outage_start",
              "outage_end", "mw_unavailable"]].head(10).to_string(index=False))
