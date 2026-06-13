# European Power Plant Outages — Cleaned (ENTSO-E)

**Every European generation-unit outage from the ENTSO-E Transparency Platform, flattened out of its
nested `Unavailability_MarketDocument` XML into one clean, analysis-ready table** — with fuel type,
planned-vs-forced, MW and MWh unavailable, and duration pre-computed.

> The raw ENTSO-E outage feed ships as **ZIP archives of deeply-nested XML**, one document per filing,
> with capacity split into nominal-vs-available, fuels as codes (`B14`), zones as EIC strings, and a
> short per-request cap that forces you to chunk hundreds of calls. Turning years of it into a table is
> days of miserable parsing. **This is that work, done — load one file.**

This repo hosts a **free sample**: one showcase zone (**France**, all years) of both deliverables —
`outages_sample.parquet` (one row per outage) **and** `daily_curve_sample.parquet` (the pre-aggregated
daily MW-offline curve).

> 👉 **Full dataset — all 38 EU bidding zones, 2018–2026 (100k+ outages) + the daily MW-offline curve —
> launching in the next few days.** ⭐ **Star / watch this repo to get notified when it's live.**

## Who uses it
Power traders & energy quants (outage features for price/imbalance models), BESS & flexibility operators
(scarcity windows), and researchers (clean panel data on European generation availability). Unplanned
outages — a nuclear trip, a 1 GW CCGT going offline — are among the biggest drivers of power and imbalance
prices, and historically the hardest piece to assemble.

## Schema (one row = one outage)
| column | type | description |
|---|---|---|
| `outage_id` | str | Stable filing id (ENTSO-E mRID) |
| `zone` | str | Bidding zone (`FR`, `DE_LU`, `NL`, `IT_NORD`, …) |
| `country` | str | Country of the unit |
| `unit_name`, `unit_eic` | str | Plant/unit name + EIC code |
| `fuel` | str | Decoded production type (`Nuclear`, `Fossil Gas`, `Wind Offshore`, …) |
| `status` | str | `planned` or `forced` (unplanned) |
| `outage_start`, `outage_end` | timestamp (UTC) | Outage window (as currently filed) |
| `duration_hours` | float | end − start |
| `nominal_mw`, `available_mw` | float | Unit nominal capacity, capacity still available |
| `mw_unavailable` | float | **nominal − available** — capacity offline |
| `mwh_unavailable` | float | mw_unavailable × duration |
| `last_updated`, `revision` | — | When ENTSO-E last (re)published the filing |

Full field docs: [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

## Load it (a few lines)
```python
import pandas as pd
df = pd.read_parquet("outages_sample.parquet")              # one row per outage
fr_nuclear_trips = df[(df.fuel == "Nuclear") & (df.status == "forced")]

curve = pd.read_parquet("daily_curve_sample.parquet")       # daily MW offline by fuel — ready to plot
curve[curve.fuel == "Nuclear"].plot(x="date", y="mw_offline")   # French nuclear offline over time
```
More loaders (DuckDB / Polars) in [`load_example.py`](load_example.py).

## Quality
Every build passes an automated QC suite (schema, `mw_unavailable ≥ 0` and `≤ nominal`, positive
durations, decoded fuels, coverage per zone, internal consistency).

## Honest notes
- Rows reflect the **currently-filed** state of each outage (ENTSO-E returns the latest version; the
  historical dump can't reconstruct *what was known on a past date*).
- Source: **ENTSO-E Transparency Platform** (documentType A80, generation unavailability). This is a
  derived, cleaned redistribution — attribute ENTSO-E as the data source.
- No personal data (subjects are power plants); GDPR N/A.

## License
Data: CC-BY-4.0 (attribute ENTSO-E). See source terms on the ENTSO-E Transparency Platform.
