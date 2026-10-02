# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-03 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 1797.8 | 1773.8 | 1811.2 |
| `create_greffes_variable` | raw | 5 | 59.1 | 58.2 | 60.5 |
| `create_blood_rh_variable` | raw | 5 | 62.7 | 61.9 | 63.5 |
| `create_hla_compatibility_variable` | raw | 5 | 62.2 | 61.6 | 62.3 |
| `process_prep_regimen_variables` | raw | 5 | 25.3 | 23.8 | 25.5 |
| `process_prophylaxis_drugs` | raw | 5 | 504.5 | 501.6 | 516.7 |
| `process_upset_plot` | raw | 5 | 564.3 | 562.7 | 568.3 |
| `competing_risks_agvhd_100d` | processed | 3 | 923.4 | 915.8 | 937.0 |
| `km_survival_lifelines` | processed | 5 | 58.9 | 58.2 | 614.5 |
| `json_store_roundtrip` | processed | 5 | 232.7 | 228.9 | 249.1 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
