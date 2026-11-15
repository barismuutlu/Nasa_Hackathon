🔥 SPACE APPS 2026 – TASK DISTRIBUTION 🛰️
Lead: P4 Barış (integration + quick decisions)

━━━━━━━━━━━━━━━━━━
🟦 DATA & SCIENCE TEAM
━━━━━━━━━━━━━━━━━━

P1 – Data Engineer: SÜLEYMAN
📁 pipeline/ingest.py
* Read the FIRMS CSVs (MODIS + VIIRS S-NPP/N20/N21)
* Merge archive + nrt, delete duplicates (on overlap, archive stays)
* Convert to the shared schema → data/hotspots.parquet
⏰ 11:30 sample file (1 region, 1 year) → everyone
⏰ 12:30 full data + satellite first/last date table → Bahtiyar

P2 – Harmonization: BAHTİYAR
📁 pipeline/harmonize.py
* MODIS/VIIRS counts per grid (0.25°) + month
* Method A: k = MODIS / VIIRS (latitude band × local season × satellite)
* weight_harm = k / number of active VIIRS satellites
* Training: Argentina 2012–2021, application: everywhere
⏰ 14:30 k_factors.csv → Oğuzhan
⏰ 16:30 harmonized data ready

P3 – ML & Validation: OĞUZHAN
📁 pipeline/validate.py
* Training 2012–2021, test 2022–2024
* Metrics: R², bias + predicted-vs-actual plot
* Check: are Venn August 2026 + April 2011 visible?
* If time allows: Method B (logistic regression)
⏰ 19:00 validation results → İbrahim

━━━━━━━━━━━━━━━━━━
🟩 APP TEAM
━━━━━━━━━━━━━━━━━━

P4 – Data Layer + LEAD: BARIŞ
📁 app/query.py + CLAUDE.md
* 08:55 push CLAUDE.md, .gitignore, requirements.txt, folders
* 11:00 mock parquet → Yusuf
* get_hotspots(), monthly_matrix(), anomaly(), to_csv_bytes()
⏰ 16:30 working with real data

P5 – Interface: YUSUF
📁 app/app.py
* Streamlit: map + region drawing (streamlit-folium)
* Calendar heatmap: month × year, viridis (plotly)
* Anomaly card, raw/harmonized toggle, CSV download
* Preset regions: Aachen/Eifel + La Rioja + Hohes Venn
* Publish to Streamlit Cloud (Sunday morning)
⏰ 16:30 raw calendar working
⏰ 19:00 MVP ready

━━━━━━━━━━━━━━━━━━
🟨 STORY TEAM
━━━━━━━━━━━━━━━━━━

P6 – Presentation & Testing: İBRAHİM
📁 docs/pitch/
* Slides (~4 min pitch), 6 FIRMS images
* Worldview: MODIS vs VIIRS on the same day
* Project page text
* Demo scenario + test the app like a user
* Timekeeping ⏱️
⏰ Sunday 14:00 presentation ready

━━━━━━━━━━━━━━━━━━
⏰ CHECKPOINTS (5 min)
━━━━━━━━━━━━━━━━━━
10:30 Roles + schema + repo ready
13:00 Real data with everyone, mock app up and running
16:30 ✅ Raw calendar end-to-end
19:00 ✅ Harmonized MVP
Sunday 09:15 Judging criteria
Sunday 12:00 ❄️ FEATURE FREEZE
Sunday 14:30 📤 SUBMISSION (deadline 15:00)

━━━━━━━━━━━━━━━━━━
🤖 CLAUDE SETUP (everyone, 1 time)
━━━━━━━━━━━━━━━━━━
git clone … && cd …
echo "@ekip/P1_Suleyman.CLAUDE.md" > CLAUDE.local.md   ← write your own file
(P2_Bahtiyar / P3_Oguzhan / P4_Baris / P5_Yusuf / P6_Ibrahim)

━━━━━━━━━━━━━━━━━━
📌 RULES
━━━━━━━━━━━━━━━━━━
* Everyone works ONLY in their own file
* Schema change → ask Barış first
* Before committing: git pull --rebase
* A small commit every 30–60 min, git add only your own file
* Check the agent's code before committing
* Stuck? Don't spend more than 15 min on it, say so!
