# Validation summary

Input: `data/hotspots_harm.parquet`  
monthly_grid.parquet consistent with annual n_modis/n_viirs ✓  
k_factors.csv: 49 rows. Confirmed by P2: k only from Argentina 2012–2021 VIIRS, Terra-only weight from 2003–2011 → test years (2022–2024) did not enter k.

## Test (cell-month, harmonized vs raw VIIRS)

test = 2022–2024; test_2022 = before NOAA-21; test_2023-2024 = NOAA-21 active (satellite not in training); transfer_2012-2026 = all VIIRS years of Aachen/Eifel (the region never entered training).

| region | period | scale | method | R² | bias (detections/cell-month) | bias % | n |
|---|---|---|---|---|---|---|---|
| aachen_eifel | test | 0.25deg | harm | 0.49 | -0.01 | -1.6 | 14 |
| aachen_eifel | test | 0.25deg | raw_viirs | -112.83 | 4.21 | +842.9 | 14 |
| aachen_eifel | test | 1deg | harm | 0.57 | -0.01 | -1.6 | 12 |
| aachen_eifel | test | 1deg | raw_viirs | -119.27 | 4.92 | +842.9 | 12 |
| aachen_eifel | test_2022 | 0.25deg | harm | -0.40 | -0.50 | -66.0 | 4 |
| aachen_eifel | test_2022 | 0.25deg | raw_viirs | -1.55 | 0.75 | +100.0 | 4 |
| aachen_eifel | test_2022 | 1deg | harm | -0.85 | -0.66 | -66.0 | 3 |
| aachen_eifel | test_2022 | 1deg | raw_viirs | -4.50 | 1.00 | +100.0 | 3 |
| aachen_eifel | test_2023-2024 | 0.25deg | harm | 0.76 | 0.19 | +46.8 | 10 |
| aachen_eifel | test_2023-2024 | 0.25deg | raw_viirs | -154.00 | 5.60 | +1400.0 | 10 |
| aachen_eifel | test_2023-2024 | 1deg | harm | 0.88 | 0.21 | +46.8 | 9 |
| aachen_eifel | test_2023-2024 | 1deg | raw_viirs | -157.35 | 6.22 | +1400.0 | 9 |
| aachen_eifel | transfer_2012-2026 | 0.25deg | harm | 0.63 | 0.86 | +35.0 | 68 |
| aachen_eifel | transfer_2012-2026 | 0.25deg | raw_viirs | -258.09 | 30.90 | +1250.6 | 68 |
| aachen_eifel | transfer_2012-2026 | 1deg | harm | 0.79 | 1.09 | +35.0 | 54 |
| aachen_eifel | transfer_2012-2026 | 1deg | raw_viirs | -209.94 | 38.91 | +1250.6 | 54 |
| argentina | test | 0.25deg | harm | 0.64 | 0.23 | +6.7 | 51250 |
| argentina | test | 0.25deg | raw_viirs | -87.01 | 26.88 | +785.9 | 51250 |
| argentina | test | 1deg | harm | 0.79 | 1.37 | +6.7 | 8616 |
| argentina | test | 1deg | raw_viirs | -74.82 | 159.88 | +785.9 | 8616 |
| argentina | test_2022 | 0.25deg | harm | 0.51 | 0.81 | +18.4 | 17633 |
| argentina | test_2022 | 0.25deg | raw_viirs | -85.37 | 31.07 | +706.7 | 17633 |
| argentina | test_2022 | 1deg | harm | 0.71 | 5.02 | +18.4 | 2834 |
| argentina | test_2022 | 1deg | raw_viirs | -71.96 | 193.31 | +706.7 | 2834 |
| argentina | test_2023-2024 | 0.25deg | harm | 0.85 | -0.07 | -2.5 | 33617 |
| argentina | test_2023-2024 | 0.25deg | raw_viirs | -90.31 | 24.68 | +848.7 | 33617 |
| argentina | test_2023-2024 | 1deg | harm | 0.93 | -0.42 | -2.5 | 5782 |
| argentina | test_2023-2024 | 1deg | raw_viirs | -80.45 | 143.49 | +848.7 | 5782 |

## Test years one by one (Σ harmonized VIIRS / Σ MODIS; 1.00 = perfect)

| region | year | Σ MODIS | Σ harm | ratio |
|---|---|---|---|---|
| aachen_eifel | 2022 | 3 | 1.0 | 0.34 |
| aachen_eifel | 2023 | 4 | 5.4 | 1.35 |
| aachen_eifel | 2024 | 0 | 0.5 | — |
| argentina | 2022 | 77522 | 91757.8 | 1.18 |
| argentina | 2023 | 47911 | 48672.8 | 1.02 |
| argentina | 2024 | 49843 | 46627.3 | 0.94 |

### Argentina 2022 monthly (S-NPP Jul–Aug, Aqua Mar–Apr outages)

| month | Σ MODIS | Σ harm | ratio | Terra | Aqua | SNPP | NOAA20 |
|---|---|---|---|---|---|---|---|
| January | 14485 | 17352.1 | 1.20 | 5907 | 8578 | 62411 | 59091 |
| February | 10260 | 11974.3 | 1.17 | 4482 | 5778 | 43248 | 40303 |
| March | 1778 | 1750.7 | 0.98 | 896 | 882 | 6817 | 6708 |
| April | 831 | 1070.8 | 1.29 | 421 | 410 | 4370 | 4310 |
| May | 1280 | 1256.9 | 0.98 | 397 | 883 | 4923 | 5073 |
| June | 1918 | 2143.5 | 1.12 | 336 | 1582 | 6881 | 7382 |
| July | 4076 | 3930.7 | 0.96 | 959 | 3117 | 9556 | 13295 |
| August | 11050 | 12034.6 | 1.09 | 3044 | 8006 | 34624 | 39462 |
| September | 13121 | 13476.2 | 1.03 | 4345 | 8776 | 46795 | 45763 |
| October | 6478 | 8441.3 | 1.30 | 2006 | 4472 | 28635 | 29269 |
| November | 7981 | 12666.9 | 1.59 | 3118 | 4863 | 44476 | 42067 |
| December | 4264 | 5659.7 | 1.33 | 1982 | 2282 | 20178 | 19717 |

## 2022 deviation — diagnosis from raw data (Argentina)

ratio = MODIS / (VIIRS per active VIIRS satellite). Independent of harmonization. Training-year range 0.280–0.326 (median 0.299).

| year | MODIS | VIIRS/satellite | ratio | ratio / training median | Aqua/Terra |
|---|---|---|---|---|---|
| 2012 | 61885 | 189774 | 0.326 | 1.09 | 1.73 |
| 2013 | 66553 | 237549 | 0.280 | 0.94 | 1.67 |
| 2014 | 36817 | 126344 | 0.291 | 0.97 | 1.48 |
| 2015 | 45140 | 151064 | 0.299 | 1.00 | 1.75 |
| 2016 | 55414 | 181412 | 0.305 | 1.02 | 1.84 |
| 2017 | 60301 | 201660 | 0.299 | 1.00 | 1.64 |
| 2018 | 55410 | 183612 | 0.302 | 1.01 | 1.73 |
| 2019 | 50388 | 161172 | 0.313 | 1.05 | 1.75 |
| 2020 | 124103 | 441532 | 0.281 | 0.94 | 1.87 |
| 2021 | 56876 | 198512 | 0.287 | 0.96 | 1.74 |
| 2022 (test) | 77522 | 312677 | 0.248 | 0.83 | 1.78 |
| 2023 (test) | 47911 | 167013 | 0.287 | 0.96 | 1.60 |
| 2024 (test) | 49843 | 155388 | 0.321 | 1.07 | 2.06 |

2022 monthly ratio / training median of the same month (< 1 → fewer MODIS than expected): Jan 0.76, Feb 0.87, Mar 1.06, Apr 0.77, May 0.93, Jun 0.92, Jul 1.18, Aug 0.91, Sep 0.92, Oct 0.79, Nov 0.64, Dec 0.76

## Hohes Venn (box lon 5.95–6.25, lat 50.45–50.60)

'Visible' = value > 0 and ≥ 3 times the mean of the same month in the other years.

| series | month | result | visible |
|---|---|---|---|
| raw | 2011-04 | 17 detections — highest April of 26 years; 6 times the mean of the same month in other years (≈2.6), other years max 12 | yes |
| raw | 2026-08 | 1,899 detections — highest August of 26 years; 23,738 times the mean of the same month in other years (≈0.1), other years max 2 | yes |
| modis | 2011-04 | 17 MODIS detections — highest April of 26 years; 27 times the mean of the same month in other years (≈0.6), other years max 3 | yes |
| modis | 2026-08 | 105 MODIS detections — highest August of 26 years; 1,312 times the mean of the same month in other years (≈0.1), other years max 2 | yes |
| harm | 2011-04 | 17 MODIS-equivalent detections — highest April of 26 years; 29 times the mean of the same month in other years (≈0.6), other years max 3 | yes |
| harm | 2026-08 | 169 MODIS-equivalent detections — highest August of 26 years; 2,115 times the mean of the same month in other years (≈0.1), other years max 2 | yes |

### Supporting evidence: MCD64A1 burned area (P1, `data/burned_area_check.csv`)

Does the detection fall on a pixel (3×3 neighbourhood ≈ 1.4 km) that MCD64A1 (monthly burned area, ~500 m) marks as burned within ±16 days? **Not an independent validation**: the MCD64A1 algorithm also uses MODIS active fire data and can miss small burns. 'unknown' (unknown/no_data) ≠ 'unburned'.

| event | instrument | matched | unburned | burned at another time | unknown | total |
|---|---|---|---|---|---|---|
| April 2011 | MODIS | 9 (53%) | 8 | 0 | 0 | 17 |
| August 2026 | MODIS | 93 (89%) | 12 | 0 | 0 | 105 |
| August 2026 | VIIRS | 1674 (93%) | 120 | 0 | 0 | 1794 |

## 3 sentences for the presentation (P6)

1. In Argentina (training region), for the years 2022–2024 not used in training, the harmonized VIIRS estimate predicts the MODIS detection count at 1° cell-month scale with R²=0.79 and a total bias of +6.7%.
   In 2023–2024, when NOAA-21 (never seen in training) is also active: R²=0.93, total bias -2.5% (2022, before NOAA-21: R²=0.71, +18.4%).
2. Transferred unchanged to Aachen/Eifel (2012–2026), the same coefficients give R²=0.79, total bias +35.0% (n=54 cell-months); this R² comes largely from a single event (August 2026): excluding that month R²=0.37, bias -4.3%.
3. In the Hohes Venn, detection increases coinciding with known fire events are visible in the harmonized calendar in April 2011 and August 2026: April 2011 → 17 MODIS-equivalent detections — highest April of 26 years; 29 times the mean of the same month in other years (≈0.6), other years max 3; August 2026 → 169 MODIS-equivalent detections — highest August of 26 years; 2,115 times the mean of the same month in other years (≈0.1), other years max 2.

## Limitations and future work

- **2022 (test) over-estimation:** in Argentina Σharm/ΣMODIS = 1.18. The excess is in the fire season (Jan 1.20, Feb 1.17, Apr 1.29, Oct 1.30, Nov 1.59, Dec 1.33); the other months, including outage months, are close to 1 (Mar 0.98, May 0.98, Jun 1.12, Jul 0.96, Aug 1.09, Sep 1.03). In the raw data, too, the 2022 MODIS/VIIRS ratio lies outside the training range (diagnosis table above) → not explained by the S-NPP/Aqua outages or a persistent orbital drift (2023–2024 return to normal).
- **Aachen/Eifel August 2026 (region transfer, single event, small n):** harm/MODIS = 1.61 (169 / 105). Not caused by the fallback (P2: even with the 40–50° band k it is +50%); the event's implied k is 0.176, all training k values are ≥ 0.20.
- **Transfer R² is driven by a single event:** Aachen/Eifel 1° R²=0.79 (n=54, bias +35.0%); excluding 2026-08 R²=0.37, bias -4.3% (n=52). So in ordinary periods the total level holds but the cell-month pattern is weak; the large event is over-estimated.
- **Interpretation (hypothesis, not validated):** k depends on fire size — on a single large fire front VIIRS (375 m) counts disproportionately many pixels compared with MODIS (1 km); k is stratified only by latitude band × season × satellite, so it cannot capture this.
- **Future work:** condition k on fire size (area / total FRP of the same-day cluster of neighbouring detections); a second training region in Europe for transfer.
- **Sample size:** Aachen/Eifel has only 7 MODIS detections in 2022–2024 → the regional test metric is statistically meaningless; hence transfer_2012-2026 is reported.
