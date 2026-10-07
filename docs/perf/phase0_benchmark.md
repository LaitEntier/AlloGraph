# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-07 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 212.9 | 208.3 | 217.5 |
| `create_greffes_variable` | raw | 5 | 8.2 | 7.4 | 8.5 |
| `create_blood_rh_variable` | raw | 5 | 13.4 | 12.9 | 14.9 |
| `create_hla_compatibility_variable` | raw | 5 | 23.7 | 22.3 | 25.2 |
| `process_prep_regimen_variables` | raw | 5 | 25.6 | 24.6 | 28.0 |
| `process_prophylaxis_drugs` | raw | 5 | 28.9 | 26.6 | 36.3 |
| `process_upset_plot` | raw | 5 | 28.3 | 27.3 | 29.1 |
| `competing_risks_agvhd_100d` | processed | 3 | 87.7 | 86.9 | 89.2 |
| `km_survival_lifelines` | processed | 5 | 58.2 | 57.5 | 629.4 |
| `json_store_roundtrip` | processed | 5 | 258.6 | 251.5 | 287.1 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
