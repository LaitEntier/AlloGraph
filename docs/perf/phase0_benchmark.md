# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-07 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 415.1 | 404.5 | 461.2 |
| `create_greffes_variable` | raw | 5 | 65.5 | 63.0 | 66.4 |
| `create_blood_rh_variable` | raw | 5 | 67.6 | 66.5 | 86.6 |
| `create_hla_compatibility_variable` | raw | 5 | 65.6 | 64.8 | 68.2 |
| `process_prep_regimen_variables` | raw | 5 | 31.1 | 26.3 | 37.1 |
| `process_prophylaxis_drugs` | raw | 5 | 30.2 | 30.1 | 34.3 |
| `process_upset_plot` | raw | 5 | 29.3 | 28.9 | 30.8 |
| `competing_risks_agvhd_100d` | processed | 3 | 1390.3 | 1383.2 | 1394.3 |
| `km_survival_lifelines` | processed | 5 | 61.8 | 60.3 | 696.7 |
| `json_store_roundtrip` | processed | 5 | 287.1 | 272.3 | 311.5 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
