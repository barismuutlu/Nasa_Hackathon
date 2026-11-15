# P6 — Presentation & Testing: İbrahim

Shared rules and the schedule are in the root `CLAUDE.md`, the terminology is in **`docs/CONTRACT.md` §8**. This file covers only your role.

## Files you own (Claude writes ONLY to these)
- `docs/pitch/` (slides, images, texts, demo scenario, test notes)

## Task
1. **Pitch (~4 min)** — `docs/pitch/slides/` + `docs/pitch/script.md` (speech text, second by second).
   Suggested flow:
   1. Problem (30 s): 25-year fire record, satellites change → fake trend
   2. Evidence (30 s): MODIS vs VIIRS Worldview image of the same day
   3. Solution (60 s): the harmonization idea (k = MODIS/VIIRS, dividing by the number of active satellites)
   4. Demo (60 s): Hohes Venn → April 2011 & August 2026; La Rioja raw ↔ harmonized
   5. Validation (30 s): Oğuzhan's R², bias, predicted-vs-actual plot
   6. Impact + next step (30 s)
2. **6 FIRMS images** — `docs/pitch/img/`: date + satellite + region in the file name
   (e.g. `2026-08-xx_VIIRS_HohesVenn.png`). Source/attribution note in `docs/pitch/img/SOURCES.md`.
3. **Worldview** — same day, same region, MODIS vs VIIRS fire layer side by side.
4. **Project page text** — `docs/pitch/project_page.md` (background ready; summary, method, data
   sources: NASA FIRMS MODIS C6.1 + VIIRS C2, tools, team).
5. **Demo scenario** — `docs/pitch/demo.md`: click-by-click steps + a backup in case the internet goes down
   (screen recording / screenshots).
6. **User test** — after the 19:00 MVP, use the app like a stranger.
   Write the bugs into `docs/pitch/test_notes.md`: step, expected, actual, to whom (Yusuf/Barış).
7. **Timekeeping ⏱️** — remind the group 10 min before every checkpoint; Sunday 12:00 freeze,
   14:30 submission.

## Inputs you will wait for
| Time | What | From whom |
|---|---|---|
| 16:30 | Raw vs harmonized annual plot | Bahtiyar (P2) |
| 19:00 | `docs/validation/` + 3-sentence summary | Oğuzhan (P3) |
| 19:00 | MVP (for testing) | Yusuf (P5) |
| Sunday 10:00 | Live link | Yusuf (P5) |

## Submissions
| Time | What |
|---|---|
| 19:00 | Slide draft (with images) |
| Sunday 09:15 | Judging criteria ↔ slide mapping table |
| Sunday 13:00 | Rehearsal (timed, < 4 min) |
| Sunday 14:00 | Presentation + project page + demo video ready |

## Note for Claude
- Do not write to code files (`pipeline/`, `app/`). If you see a bug in the app, write it into test_notes.
- Do not make up numbers (R², bias, counts); take them only from `docs/validation/metrics.json`,
  otherwise leave `[TBD — Oğuzhan]`.
- Do not use the NASA logo in the images; write "NASA FIRMS / Worldview" as the source.
- Terminology (CONTRACT §8): detection/hotspot ≠ validated fire event. Do not present the harmonization
  as "validated"; describe it with numbers, like "calibrated in Argentina, R²=… in the 2022–2024 test".
- Screenshots from synthetic (mock) data do not go into the presentation (if the page has the "SYNTHETIC" warning, do not use it).
