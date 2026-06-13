# Data Dictionary — European Power Plant Outages

One row = one outage filing (current state) from the ENTSO-E Transparency Platform
(`Unavailability_MarketDocument`, documentType **A80** generation + **A77** production unavailability).

## Main table (`outages_all.parquet`, and `zone=…/year=…` partitions)

| column | type | unit | description |
|---|---|---|---|
| `outage_id` | string | — | Stable filing identifier (ENTSO-E document `mRID`). One row per current filing. |
| `zone` | string | — | ENTSO-E bidding zone code, human form: `NL`, `BE`, `DE_LU`, `FR`, `AT`. |
| `country` | string | — | Country named in the filing (`production_RegisteredResource.location.name`). |
| `unit_name` | string | — | Plant / unit name, e.g. `DOEL 4`, `Zandvliet Power`. May be blank in some filings. |
| `unit_eic` | string | — | EIC code of the production resource — the stable machine ID for the unit. |
| `fuel` | string | — | Decoded production type (see psrType map below), e.g. `Nuclear`, `Fossil Gas`, `Wind Offshore`, `Hydro Pumped`, `Storage`. |
| `psr_type` | string | — | Raw ENTSO-E `psrType` code (`B01`–`B25`); kept for traceability. |
| `status` | string | — | `planned` (businessType **A53**) or `forced` (unplanned, businessType **A54**). |
| `doc_type` | string | — | `A80` (generation unavailability) or `A77` (production unavailability). |
| `outage_start` | timestamp (UTC) | — | Start of the unavailability window. |
| `outage_end` | timestamp (UTC) | — | End of the unavailability window, **as currently filed** (this is the field most often revised). |
| `duration_hours` | float | h | `outage_end − outage_start`. |
| `nominal_mw` | float | MW | Nominal capacity of the unit (`…powerSystemResources.nominalP`). |
| `available_mw` | float | MW | Capacity still available during the outage (`0` = full outage). Min across the available-period profile. |
| `mw_unavailable` | float | MW | **Headline figure:** `nominal_mw − available_mw` — the capacity taken offline. |
| `mwh_unavailable` | float | MWh | `mw_unavailable × duration_hours` — energy not produced over the window. |
| `last_updated` | timestamp (UTC) | — | When ENTSO-E last (re)published this filing (`createdDateTime`). |
| `revision` | int | — | ENTSO-E `revisionNumber` of the current filing. |

## Companion table (`daily_curve/zone=…/year=…`)
Pre-aggregated **MW offline per zone × fuel × day** — the feature most price/imbalance models actually use.

| column | type | unit | description |
|---|---|---|---|
| `zone` | string | — | Bidding zone. |
| `date` | date (UTC) | — | Calendar day. |
| `fuel` | string | — | Decoded production type. |
| `mw_offline` | float | MW | Total `mw_unavailable` from all outages overlapping that day for that zone+fuel. |
| `mw_offline_forced` | float | MW | Of which from **forced** (unplanned) outages only. |
| `n_outages` | int | — | Number of distinct outages overlapping that day. |

## psrType → fuel map
`B01` Biomass · `B02` Fossil Brown coal/Lignite · `B03` Fossil Coal-derived gas · `B04` Fossil Gas ·
`B05` Fossil Hard coal · `B06` Fossil Oil · `B07` Fossil Oil shale · `B08` Fossil Peat · `B09` Geothermal ·
`B10` Hydro Pumped Storage · `B11` Hydro Run-of-river · `B12` Hydro Water Reservoir · `B14` Nuclear ·
`B15` Other renewable · `B16` Solar · `B17` Waste · `B18` Wind Offshore · `B19` Wind Onshore ·
`B20` Other · `B25` Energy storage.

## businessType
`A53` = planned outage · `A54` = forced / unplanned outage. (Surfaced as `status`.)

## Notes / quality
- Timestamps are **UTC**. ENTSO-E `date` + `time` fields are joined into a single timestamp.
- `available_mw` is taken as the **minimum** of the available-period profile (deepest reduction) so
  `mw_unavailable` is the maximum capacity offline during the window; the full sub-period profile is
  available in the subscription edition.
- Rows are **not** de-duplicated across overlapping query windows beyond `(outage_id, revision)`; one row
  = the current filed state of one outage.
- Missing fields (unnamed units, absent nominal capacity) are preserved as null, not dropped.
- **No personal data**: subjects are power plants and corporations, which have no privacy rights (GDPR
  N/A).
