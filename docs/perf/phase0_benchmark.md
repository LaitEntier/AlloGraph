# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-07 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 419.2 | 408.9 | 426.3 |
| `create_greffes_variable` | raw | 5 | 64.0 | 62.2 | 67.4 |
| `create_blood_rh_variable` | raw | 5 | 65.8 | 64.6 | 66.6 |
| `create_hla_compatibility_variable` | raw | 5 | 66.0 | 63.2 | 66.7 |
| `process_prep_regimen_variables` | raw | 5 | 26.4 | 25.9 | 27.1 |
| `process_prophylaxis_drugs` | raw | 5 | 29.0 | 28.2 | 29.8 |
| `process_upset_plot` | raw | 5 | 28.6 | 27.6 | 30.3 |
| `competing_risks_agvhd_100d` | processed | 3 | 82.6 | 82.3 | 85.0 |
| `km_survival_lifelines` | processed | 5 | 58.7 | 57.4 | 634.2 |
| `json_store_roundtrip` | processed | 5 | 263.3 | 251.9 | 300.8 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
