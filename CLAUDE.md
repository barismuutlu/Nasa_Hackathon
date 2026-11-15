# CLAUDE.md — Space Apps 2026: MODIS ↔ VIIRS Fire Calendar

> This file is shared by the whole team. Owner: **P4 Barış**. Change → ask Barış first.

## 0. First step for Claude (MANDATORY)
1. Learn the user's role from the `CLAUDE.local.md` file (in gitignore, on everyone's own machine).
2. If `CLAUDE.local.md` does not exist, ask the user **"Which role are you (P1–P6)?"**, then
   read the corresponding file under `ekip/` and suggest the user create `CLAUDE.local.md` with this content:
   ```
   @ekip/P1_Suleyman.CLAUDE.md
   ```
3. **Write only to the files that role owns.** If a change is needed in someone else's file,
   do not write the code; give the user a short note: "tell this person this".
4. If a schema or API (`docs/CONTRACT.md`) change is needed: stop, tell the user "ask P4 first".
5. For every submission that affects someone else, apply the **§8 Submission Protocol** (test → approval → push → prompt).
6. If the user pastes a prompt with a `[Px Name → Py Name]` header: first `git pull --rebase`,
   then run the CHECK step in the prompt, show the result to the user, then move on to WHAT YOU NEED TO DO.

## 1. Project
A **consistent monthly detection calendar** for 2000–2026 from NASA FIRMS active fire **detections**.
Problem: MODIS (Terra/Aqua, 2000→) and VIIRS (S-NPP 2012→2026-11-02, NOAA-20 2018→, NOAA-21 2023→) have different
sensitivities; every new satellite creates an **artificial jump** in the raw counts. We convert VIIRS detections
into **MODIS-equivalent** units (harmonization) and show a continuous series.
The harmonization coefficients are **an unvalidated hypothesis**; until P3's test metrics (2022–2024)
arrive they are not presented as "correct/calibrated", and after the metrics arrive they are presented together with their numbers.

Main visual of the pitch: 2012/2018/2023 jumps in the raw calendar → absent in the harmonized calendar.
Validation story: detection increases that coincide with known fire events in the Hohes Venn
should appear in the calendar in **April 2011** and **August 2026**. (Detection ≠ validated fire event.)

## 2. Team & file ownership
| Role | Person | Files owned |
|---|---|---|
| P1 Data Engineer | Süleyman | `pipeline/ingest.py`, `pipeline/weather_power.py` (NASA POWER, experimental), `pipeline/burned_area_check.py` (MCD64A1 supporting check, does not touch the main schema), `data/sample/` |
| P2 Harmonization | Bahtiyar | `pipeline/harmonize.py`, `forecast/` (monthly prototype, EXPERIMENTAL; the 30-day view in the app is `pipeline/forecast.py`) |
| P3 ML & Validation | Oğuzhan | `pipeline/validate.py`, `docs/validation/` |
| P4 Data Layer + LEAD | Barış | `app/query.py`, `pipeline/forecast.py` (experimental view), `docs/forecast/`, `contract.py`, `docs/CONTRACT.md`, `tests/`, `README.md`, `CLAUDE.md`, `ekip/`, `requirements.txt`, `.gitignore`, `data/mock/`, `data/deploy/` |
| P5 Interface | Yusuf | `app/app.py`, `.streamlit/config.toml` |
| P6 Presentation & Testing | İbrahim | `docs/pitch/` |

If a package needs to be added to shared files (`requirements.txt` etc.) → tell Barış; Barış adds it.

**Additional permission (P4 approval, 14 Nov):** P2 Bahtiyar: until the freeze, contributes to `app/` and `docs/pitch/` only via a `p2/*` branch;
merge is up to the file owner (Yusuf / İbrahim). Before starting on `app/app.py`, Bahtiyar tells Yusuf which section it is.
P3 Oğuzhan left early on the evening of 14 Nov, back on the team on 15 Nov; `pipeline/validate.py` and `docs/validation/` stay with P3.

## 3. Data contract (LOCKED — changes only with P4 approval; version: header of `docs/CONTRACT.md`)
Full schema, repetition rules, region names, pipeline inputs/outputs and the `query.py` API:
**`docs/CONTRACT.md`** (imported below). Code counterpart: **`contract.py`**
(constants + `validate_hotspots(df, stage)`). P1 and P2 call the validator before writing parquet.

@docs/CONTRACT.md

Reminder (most common mistake):
- Columns use FIRMS names: `latitude`, `longitude`, `brightness`, `confidence` (**original value**),
  `type`. For the class, `confidence_class`.
- One row = one **detection** (thermal anomaly), not a validated fire event (CONTRACT §8).
- `weight_harm` is NaN at ingest; the method belongs to P2, its validation to P3 (CONTRACT §6).

### 3.1 File locations
```
contract.py       schema constants + validator (P4)
data/raw/<region>/  FIRMS CSVs, folder name = region slug (does NOT go into git)
data/sample/      P1's sample file (small, goes into git)
data/mock/        P4's synthetic parquet + generator (goes into git)
data/deploy/      reduced data for Streamlit Cloud (<50 MB, goes into git)
data/*.parquet, data/*.csv   full data and intermediate outputs (does NOT go into git — Drive/USB)
docs/CONTRACT.md  contract (P4)
docs/validation/  P3 outputs (png + metrics.json)
docs/forecast/    P4 experimental view outputs (CONTRACT §7.5)
docs/pitch/       P6
tests/smoke_test.py  end-to-end smoke test (P4)
```

### 3.2 Importing the shared module
`pipeline/*.py` and `app/*.py` use `contract` by adding the root directory to the import path:
```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contract import validate_hotspots
```

## 4. Environment and running
### 4.1 Everyone uses the SAME environment (MANDATORY)
- **Python 3.12** (`.python-version`) + the **pinned (==) versions** in `requirements.txt`.
  Reason: differences like pandas 2 ↔ 3 produce different dtypes from the same code → `contract.py` validation
  passes on one machine and blows up on another. Streamlit Cloud also deploys with 3.12.
- Installation with `uv` (downloads Python 3.12 itself, no admin rights needed):
  ```bash
  # if uv is missing:  Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh
  #                    Windows (PowerShell): powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  uv venv --python 3.12 .venv
  source .venv/bin/activate            # Windows: .venv\Scripts\activate
  uv pip install -r requirements.txt
  python tests/smoke_test.py           # first line (program output, Turkish): "ortam: Python 3.12 + requirements.txt sürümleri" ✅
  ```
- Claude: before running code, check that `.venv` is active and that it is Python 3.12. If not, remind
  the user of the installation; do not continue with the system Python or with `pip install <package>`.
- Extra environment: `requirements-enrich.txt` (only `pipeline/burned_area_check.py`, P1; `pyhdf`). The main app,
  `app/` and `tests/` NEVER import these packages; Streamlit Cloud does not install them.
- Adding packages/changing versions is P4 only (`requirements.txt`). When it changes, everyone
  runs `uv pip install -r requirements.txt`.

### 4.2 Running
```bash
source .venv/bin/activate
python pipeline/ingest.py        # P1 → data/hotspots.parquet
python pipeline/harmonize.py     # P2 → data/hotspots_harm.parquet, monthly_grid.parquet, k_factors.csv
python pipeline/validate.py      # P3 → docs/validation/
python pipeline/forecast.py      # P4 → data/deploy/forecast.parquet, docs/forecast/ (experimental)
python tests/smoke_test.py       # P4 → contract + query end-to-end check
streamlit run app/app.py         # P5
```
All scripts are run **from the repo root**; paths are relative to the root.

## 5. Code rules
- Python 3.12 (§4.1), pandas 3 + pyarrow. Code/variable names in English, comments may be in Turkish.
- Every pipeline script: `main()` + `if __name__ == "__main__":`, path constants at the top.
- No silent errors: unexpected column/value → explicit `ValueError`.
- If large data has to be loaded into memory at once, use `pyarrow`/`usecols`.
- If a new package is needed, do not add it; tell the user "tell Barış".

## 6. Git rules
- Before committing: `git pull --rebase`
- A small commit every 30–60 min; message with a role prefix, like `P1: merge archive+nrt`.
- `git add` only your own files (NO `git add -A`).
- Read the agent's (Claude's) code before committing and run it at least once.
- Data files (`data/raw`, large parquet) are never committed.
- Pushes that affect others are done according to §8.

## 7. Schedule (Saturday 14 November → Sunday 15 November 2026)
| Time | Checkpoint | Status |
|---|---|---|
| 08:55 | P4: push repo skeleton | ✅ |
| 10:30 | Roles + schema + repo ready (5 min meeting) | ✅ |
| 11:00 | P4: mock parquet → P5 | ✅ |
| 11:30 | P1: sample file (1 region, 1 year) | ✅ |
| 12:30 | P1: full data | ✅ |
| 13:00 | Real data with everyone, mock app up and running | ✅ |
| 16:30 | Raw calendar end-to-end (P2 harmonized data, P4 real data) | ✅ (early) |
| 19:00 | Harmonized MVP (P3 validation → P6) | ✅ (early) |
| — | Streamlit Cloud (`data/deploy/`, real + harmonized data) | ✅ (Saturday instead of Sunday morning) |
| Sunday 09:15 | Review of judging criteria | |
| Sunday 12:00 | ❄️ FEATURE FREEZE — bug fixes only | |
| Sunday 14:00 | Presentation ready | |
| Sunday 14:30 | 📤 SUBMISSION (deadline 15:00) | |

**Stuck? Don't spend more than 15 min on it, say so.** Claude: if the user has spent more than 15 min on the same error,
remind them of this and suggest "write to Barış".

## 8. Submission Protocol — at every important step (MANDATORY)
**Important step** = every submission that affects someone else's work: the submissions in §7, schema/API changes,
a new file/function someone else will use, a bug fix someone is waiting for.
The three steps are done in order; **no push without the user's explicit approval.**

### Step 1 — Have the user test it, get approval
- When the work is done, Claude does NOT push. It gives the user a short test list:
  - command(s) to run, ready to copy-paste
  - for each command the **expected result** (number, table, what should appear on screen)
  - the relevant items from the "Done check" in the role file
- The user runs / looks at it themselves. Step 2 is not started until **explicit approval** such as "approved", "ok push it"
  arrives. If a problem is reported, fix it → repeat Step 1.
- Claude may also run its own tests, but "my tests passed" does not replace the user's approval.

### Step 2 — Send to GitHub according to the type of change
| Type | Example | Method |
|---|---|---|
| Small | improvement in your own file, single-file bug fix | commit on `main` → `git pull --rebase` → `git push` |
| Structural | schema / API (`docs/CONTRACT.md`), shared file (`CLAUDE.md`, `requirements.txt`), new output file, multiple files | `git switch -c <role>/<topic>` (e.g. `p4/query-api`) → commit(s) → `git switch main` → `git pull --rebase` → `git merge --no-ff <branch>` → `git push` → `git branch -d <branch>` |
- `git add` only your own files. Commit message: role prefix + what changed + whom it affects.
- Structural change touching the schema/API → P4 approval first (§0 item 4).
- If a merge conflict occurs, **do not try to resolve it**: stop, tell the user in which file and with whom the conflict is.
- After the push, get the short commit hash (`git log --oneline -1`).

### Step 3 — Write a prompt for the affected teammate's Claude
After the push, write a prompt **separately for each** affected person, in a single code block, ready to copy-paste.
The receiving Claude has not seen this conversation: file paths, function names and CLAUDE.md section numbers
must be written out explicitly, and the prompt must be understandable on its own. Template:
```
[P4 Barış → P5 Yusuf] <topic> — commit <hash>

FIRST: git pull --rebase

WHAT CHANGED:
- <file>: <change>

WHAT IT MEANS FOR YOU:
- <how it affects the receiver's work>

WHAT YOU NEED TO DO:
1. <concrete step>

CHECK (run it, show the result to the user):
- <command>  →  expected: <result>

DO NOT TOUCH: <files the receiver does not own>. If there is a problem, do not write code, notify <sender>.
```
The prompt is given in the chat; the user forwards it to the person concerned via WhatsApp/Discord.
