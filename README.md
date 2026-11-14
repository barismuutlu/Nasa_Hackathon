# Harmonizing MODIS and VIIRS Active Fire Detections

**NASA Space Apps Challenge 2026 — "Harmonization of MODIS and VIIRS Hot Spots"**

> **Live demo:** https://activefiredetectioncalendar.streamlit.app/ · **Presentation:** _[link — coming soon]_

NASA's 25-year fire record was built by a changing fleet of satellites. MODIS (Terra 2000, Aqua 2002)
is nearing the end of its mission; the VIIRS instruments (Suomi NPP 2012, NOAA-20 2018, NOAA-21 2023)
are far more sensitive. Every time a new satellite comes online, **raw detection counts jump — even if
nothing changed on the ground.** A trend line drawn from raw counts shows fire activity rising sharply
after 2012; part of that is simply more, and better, sensors looking.

We built an open data pipeline and an interactive app that convert VIIRS detections into
**MODIS-equivalent counts**, so the record from 2000 to today can be read as one consistent monthly calendar.

---

## What the app shows

| View | Purpose |
|---|---|
| **Map + region drawing** | Pick a preset region or draw any polygon; detections are shown as a heat map |
| **Monthly calendar (year × month)** | Fire detection activity for every month, raw or harmonized |
| **Raw vs. harmonized annual chart** | Raw counts step up at every satellite launch (2012, 2018, 2023); the harmonized series does not |
| **Anomaly card** | How unusual a month is compared with the same calendar month in all other years (rank, multiple of normal) |
| **CSV export** | Download the selected detections or the monthly table |

## Example: Hohes Venn (High Fens), Belgium/Germany

| Event | What the data shows |
|---|---|
| **April 2011** (MODIS era) | **17 MODIS detections** on 25–26 April, 3 satellite overpasses, all classified as vegetation fire. In the harmonized series the average of the other 25 Aprils is ≈0.59 → **~29× normal, the highest April in 26 years.** In the raw series the same month looks only ~6× normal: inflated VIIRS-era counts raise the "normal". **Without harmonization, a historic event looks far more ordinary than it was.** |
| **August 2026** (VIIRS era) | For the same event (14–17 August), **105 MODIS and 1,794 VIIRS detections** (1,899 raw in total). Harmonized estimate: **169 MODIS-equivalent detections**, the highest August in 26 years. |

All 2011 detections are on the **Belgian** side of the Hohes Venn. Had we downloaded only German data,
the event would not appear at all — which is why our study areas are coordinate boxes, not countries.

## How it works

```
NASA FIRMS CSVs ──► ingest.py ──► hotspots.parquet ──► harmonize.py ──► hotspots_harm.parquet ──► app (Streamlit)
 (MODIS + 3×VIIRS,   clean, dedupe,    one schema         weight_harm         weight_harm          query.py ─► app.py
  archive + NRT)     merge archive/NRT                    per detection                                  │
                                                               │                                         ▼
                                                         validate.py ──► metrics + figures      calendar, map, anomaly
```

1. **Ingest** — all MODIS C6.1 and VIIRS C2 (S-NPP, NOAA-20, NOAA-21) detections, standard (archive) and
   near-real-time (NRT), are converted to a single schema ([docs/CONTRACT.md](docs/CONTRACT.md)).
   Exact duplicates are removed; where archive and NRT overlap, archive (higher quality) is kept, per region
   and satellite. Detections from different satellites or different overpass times are never merged.
2. **Harmonization** — every detection gets a weight `weight_harm`; the sum of weights is the estimated
   number of MODIS-equivalent detections. Method: a MODIS/VIIRS ratio `k`, calibrated in Argentina (2012–2021)
   by latitude band and local season, divided by the number of VIIRS satellites active that day. Sparse
   latitude bands are merged (at least 500 MODIS detections). NOAA-21, absent from training, uses NOAA-20's
   coefficient. In the Terra-only period (2000-11 → 2002-07) the Terra weight is 2.753, derived from the data
   (Aqua catches ~1.75× more detections than Terra). Details: [`pipeline/harmonize.py`](pipeline/harmonize.py).
3. **Validation** — coefficients are tested on years not used in training (2022–2024) and in a different
   region and hemisphere (Aachen/Eifel). Results below and in [`docs/validation/`](docs/validation/).
4. **Exploration** — a Streamlit app ([`app/app.py`](app/app.py)) built on a small query layer
   ([`app/query.py`](app/query.py)).

## Validation results

Prediction: harmonized VIIRS (`Σ weight_harm`); truth: MODIS detection count, at 1° cell × month scale.
Coefficients were learned from Argentina 2012–2021 only. Source: [`docs/validation/metrics.json`](docs/validation/metrics.json).

| Argentina | Harmonized R² | Harmonized bias | Unharmonized (raw VIIRS) bias | n (cell-months) |
|---|---|---|---|---|
| Training 2012–2021 | 0.92 | −0.9% | +390% | 27,568 |
| **Test 2022–2024** | **0.79** | **+6.7%** | **+786%** | 8,616 |
| Test 2023–2024 (NOAA-21 active, not in training) | 0.93 | −2.5% | +849% | 5,782 |
| Test 2022 | 0.71 | +18.4% | +707% | 2,834 |

- **Region transfer (Aachen/Eifel, 2012–2026, region never used in training):** R² 0.79, bias +35% (n=54).
  This R² comes largely from a single event (August 2026); excluding that month, R² 0.37, bias −4.3%. In
  ordinary periods the overall level holds, but the large event is overestimated.
- **Supporting evidence (not independent validation):** in NASA's MCD64A1 burned-area product, within ±16 days
  and a 3×3-pixel (≈1.4 km) neighbourhood, 89% (MODIS) and 93% (VIIRS) of the August 2026 detections and 9/17
  of the April 2011 detections fall on burned pixels. MCD64A1 itself uses MODIS active-fire data, so this is
  not an independent validation.

## Experimental: 30-day detection outlook

Because the harmonized series is consistent across satellite changes, it can be used for forecasting. A simple
model (seasonal normal + persistence of the last 30 days, per 1° cell, Argentina) gives a **30-day outlook of
detection counts** — not a fire forecast.

- Backtest 2015–2025 (132 start dates, each year fitted on earlier years only): **direction right 74%** of the time
  (chance 50%), 23% lower squared error than the seasonal normal, positive in every year; regional totals unbiased.
- Current outlook (data through 2026-11-12): **15 Nov – 14 Dec 2026**, Argentina ≈ 2,900 MODIS-equivalent
  detections (80% range 1,500–5,400) vs. a 10-year normal of 3,700 → *near normal*.
- NASA POWER weather and an El Niño index derived from NASA MERRA-2 were tested and **did not improve** skill
  (branch `p4/forecast-experiments`). Details: [`docs/forecast/`](docs/forecast/), [`pipeline/forecast.py`](pipeline/forecast.py).

## Data

All data comes from **NASA FIRMS** (Fire Information for Resource Management System,
https://firms.modaps.eosdis.nasa.gov/):

| Product | Satellite(s) | Period used |
|---|---|---|
| MODIS Collection 6.1 active fire (standard + NRT) | Terra, Aqua | 2000-11 → 2026-11 |
| VIIRS 375 m Collection 2 active fire (standard + NRT) | Suomi NPP | 2012-01 → 2026-11-02 (end of data stream) |
| VIIRS 375 m Collection 2 active fire (standard + NRT) | NOAA-20 | 2018-04 → 2026-11 |
| VIIRS 375 m Collection 2 active fire (standard + NRT) | NOAA-21 | 2023-03 → 2026-11 |

Study areas: **Argentina** (calibration; includes La Rioja) and **Aachen/Eifel**
(coordinate box 5.96–6.44° E, 50.44–50.83° N; includes the Hohes Venn).
Comparison imagery: NASA Worldview. Full citations and licenses: [Sources, citations and licenses](#sources-citations-and-licenses).

## Sources, citations and licenses

Every source used to build this project is listed here. All **analysis data is NASA data**; NASA Earth
science data is openly shared without restriction on use. We do not use the NASA logo or imply NASA endorsement.

**Acknowledgements.** We acknowledge the use of data from NASA's Fire Information for Resource Management
System (FIRMS), part of NASA's Earth Science Data and Information System (ESDIS). NASA POWER data were obtained
from the NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science Division.

### Data

| Source | Used for | Citation | Terms |
|---|---|---|---|
| NASA FIRMS — MODIS Collection 6.1 active fire, Terra + Aqua (standard + NRT) | core dataset | MCD14ML: [doi:10.5067/FIRMS/MODIS/MCD14ML](https://doi.org/10.5067/FIRMS/MODIS/MCD14ML); MCD14DL NRT: [doi:10.5067/FIRMS/MODIS/MCD14DL.NRT.0061](https://doi.org/10.5067/FIRMS/MODIS/MCD14DL.NRT.0061) | NASA open data |
| NASA FIRMS — VIIRS 375 m active fire, Suomi NPP / NOAA-20 / NOAA-21 (standard + NRT) | core dataset | S-NPP: [doi:10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002](https://doi.org/10.5067/FIRMS/VIIRS/VNP14IMGT_NRT.002); NOAA-20: [doi:10.5067/FIRMS/VIIRS/VJ114IMGT_NRT.002](https://doi.org/10.5067/FIRMS/VIIRS/VJ114IMGT_NRT.002); NOAA-21: VJ214IMGT_NRT, see [FIRMS](https://www.earthdata.nasa.gov/data/tools/firms) | NASA open data |
| NASA MCD64A1 v061 burned area | supporting check (`pipeline/burned_area_check.py`) | Giglio, L., Justice, C., Boschetti, L., Roy, D. (2021). *MODIS/Terra+Aqua Burned Area Monthly L3 Global 500m SIN Grid V061*. NASA EOSDIS LP DAAC. [doi:10.5067/MODIS/MCD64A1.061](https://doi.org/10.5067/MODIS/MCD64A1.061). Algorithm: Giglio et al. (2018), *Remote Sens. Environ.* 217, 72–85, [doi:10.1016/j.rse.2018.08.005](https://doi.org/10.1016/j.rse.2018.08.005) | NASA open data |
| NASA POWER, daily point API (MERRA-2: precipitation, max. temperature, humidity, skin temperature) | outlook experiments only — tested, **not used** by the shipped outlook | NASA LaRC POWER Project, https://power.larc.nasa.gov/, accessed 2026-11-14. MERRA-2: Gelaro, R. et al. (2017), *J. Climate* 30, 5419–5454, [doi:10.1175/JCLI-D-16-0758.1](https://doi.org/10.1175/JCLI-D-16-0758.1) | NASA open data |
| NASA Worldview | comparison imagery in the presentation | https://worldview.earthdata.nasa.gov/ | NASA open data |
| Map basemap in the app | background only | Imagery © Esri, Maxar, Earthstar Geographics | Esri terms of use (Esri Master License Agreement) |

### Software (open source)

| Package | License | Package | License |
|---|---|---|---|
| Python 3.12 | PSF License | streamlit | Apache-2.0 |
| pandas | BSD-3-Clause | streamlit-folium | MIT |
| numpy | BSD-3-Clause | folium (Leaflet, Leaflet.draw, Leaflet.heat) | MIT (Leaflet: BSD-2-Clause) |
| pyarrow | Apache-2.0 | plotly | MIT |
| shapely | BSD-3-Clause | scikit-learn | BSD-3-Clause |
| matplotlib | Matplotlib License (PSF-based) | uv (setup tool) | MIT / Apache-2.0 |

Exact versions: [`requirements.txt`](requirements.txt). AI assistance: see [Use of AI](#use-of-ai).

## What this is — and what it is not

- A **detection** is a satellite pixel containing a thermal anomaly. **It is not a confirmed wildfire
  event**; one fire can produce many detections, and some detections are not vegetation fires.
- The harmonized series is an **estimate**. The conversion coefficients were calibrated in one region and
  tested in another; this is not a validated global product.

### Known limitations

- **Orbital drift:** Terra and Aqua are drifting from their original overpass times, so the MODIS
  "reference" itself is less stable in recent years.
- **Suomi NPP ended on 2026-11-02**; the harmonization accounts for the number of active VIIRS satellites,
  but the months right after the change are more uncertain.
- **Terra-only period (2000-11 → 2002-07):** only one MODIS satellite was flying; the Terra weight of 2.753
  corrects for this (derived from Argentina 2003–2011 data).
- **Transferability:** coefficients calibrated in Argentina may not hold for every ecosystem. In Aachen/Eifel
  the sample is small, and for the large event (August 2026) the harmonized estimate is ~1.6× MODIS (169 / 105).
- **2022 bias:** in Argentina in 2022 the harmonized total is 18% above MODIS; in the raw data, too, the
  MODIS/VIIRS ratio is outside the training range. Satellite outages do not explain it; it returns to normal in 2023–2024.
- **Hypothesis (not validated):** the coefficient may depend on fire size. On a large fire front VIIRS
  (375 m) counts disproportionately more pixels than MODIS (1 km). Future work: condition the coefficient on
  fire-cluster size, and add a second training region in Europe.
- **NOAA-21:** absent from the training period; NOAA-20's coefficient is used (see 2023–2024 test results above).
- **Time zone:** months are assigned in UTC.

## Running locally

Requires **Python 3.12** ([`.python-version`](.python-version)); we use [uv](https://docs.astral.sh/uv/) for setup.

```bash
git clone https://github.com/barismuutlu/Nasa_Hackathon.git
cd Nasa_Hackathon
uv venv --python 3.12 .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python tests/smoke_test.py           # checks the environment, the data contract and the query layer
python -m streamlit run app/app.py
```

The repo ships a small real-data extract for the preset regions (`data/deploy/`, the same data as the live
demo), so the app runs right away. Without it, the app falls back to a **synthetic** dataset (`data/mock/`)
and shows a "SYNTHETIC TEST DATA" warning. To rebuild from scratch, download the FIRMS CSVs into
`data/raw/<region>/` and run:

```bash
python pipeline/ingest.py      # → data/hotspots.parquet
python pipeline/harmonize.py   # → data/hotspots_harm.parquet, monthly_grid.parquet, k_factors.csv
python pipeline/validate.py    # → docs/validation/
```

## Repository layout

```
app/            Streamlit app (app.py) and query layer (query.py)
pipeline/       ingest → harmonize → validate; forecast.py (experimental 30-day outlook)
contract.py     shared data schema + validator used by every pipeline step
docs/           CONTRACT.md (data contract), validation/ (results), forecast/ (outlook backtest), pitch/ (presentation)
forecast/       monthly outlook prototype (experimental)
tests/          end-to-end smoke test
data/deploy/    harmonized extract for the preset regions (used by the live demo)
data/mock/      synthetic data for development (full data is not committed)
```

Code identifiers are in English; some internal docs and code comments are in Turkish (the team's working language).

## Team

| Role | Member |
|---|---|
| Data engineering (ingest) | Süleyman |
| Harmonization | Bahtiyar |
| Validation | Oğuzhan |
| Data layer, integration, team lead | Barış |
| App / UI | Yusuf |
| Presentation and testing | İbrahim |

## Use of AI

We used AI coding assistants (Claude Code) to write and review code and documentation. All data-processing
choices, scientific assumptions and results were reviewed by the team; the validation numbers come from
running the pipeline on NASA data, not from the assistant.
