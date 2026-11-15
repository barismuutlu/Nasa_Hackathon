# P6 cloud environment check — historical record, 14 November 2026

Source: `P6_ibrahim.patch`. This report belongs to the earlier Linux cloud session; repo reference `8d5894c`, the contract at that time was v1.2. It was reported that on Cloud `git pull --rebase` completed with a fast-forward. The results below were not re-run in the Windows local environment.

The current local contract is v1.3. At the first local review `.venv/Scripts/python.exe` and `uv` were not found; local validation of Python 3.12 and the pinned packages is pending. The local status and the PowerShell commands are in [test_notes.md](test_notes.md). The synthetic smoke test on Cloud is not evidence of local or scientific validation.

## Setup reported on Cloud

Since `uv` was already installed, it was not reinstalled. There was no old `.venv`; the new environment
was created at the repo root. No extra packages were added and the pinned versions were not changed.

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
python --version
python tests/smoke_test.py
```

Interpreter checked: `.venv/bin/python`; virtual environment active.
Python version: **3.12.14**. All 10 direct dependencies in `requirements.txt`
matched the requested version:

```text
pandas==3.1.1
pyarrow==26.0.1
numpy==2.5.4
shapely==2.2.0
streamlit==1.67.0
streamlit-folium==0.27.4
folium==0.20.0
plotly==7.1.0
scikit-learn==1.9.1
matplotlib==3.11.2
```

## Smoke test result

```text
✅ ortam: Python 3.12 + requirements.txt sürümleri      Python 3.12, 10 paket
13/13 geçti/atlandı, 0 hata
```

Verbatim program output (“ortam” = environment, “sürümleri” = versions, “paket” = packages, “geçti/atlandı” = passed/skipped, “hata” = errors).

7 checks passed; 6 checks were skipped because their files do not exist yet:

- `data/hotspots.parquet`
- `data/satellite_coverage.csv`
- `data/hotspots_harm.parquet`
- `data/monthly_grid.parquet`
- `data/k_factors.csv`
- `docs/validation/metrics.json`

In the query tests the selected file was `data/mock/hotspots_mock.parquet`
(`mock=True`). This result is not an end-to-end validation with real data or a claim
of scientific success. Synthetic results are not taken into the presentation.

## Re-run of the P6 check

The CSV check script of the earlier country-year download was re-run from inside the new `.venv`:
144 files, 6,893,939 raw data rows; no rows with a broken field count and
no missing values in the checked core fields. These files are the v1.1 historical
archive; v1.2 accepts only DL_FIRE inputs. Ingest was not run.

## Selection note in the Cloud editor

In VS Code, the in-repo `.venv/bin/python` must be selected via the **Python: Select Interpreter**
command. The user's editor setting was not changed from here.

## Current data and presentation rules

- `argentina` and `aachen_eifel` regions; Aachen box
  `5.96, 50.44, 6.44, 50.83`.
- Source DL_FIRE archive + NRT; country-year CSVs are not used.
- Satellite addition periods 2012/2018/2023; NOAA-21 start 2023-03-01,
  S-NPP end 2026-11-02. The chart lines are taken from the
  `data_info()["satellite_ranges"]` values in the data.
- The transfer of the valid DL_FIRE archive into this workspace has not been done yet.
