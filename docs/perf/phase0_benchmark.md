# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-07 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 416.9 | 407.3 | 434.1 |
| `create_greffes_variable` | raw | 5 | 63.2 | 61.8 | 64.5 |
| `create_blood_rh_variable` | raw | 5 | 66.5 | 65.0 | 67.6 |
| `create_hla_compatibility_variable` | raw | 5 | 65.7 | 64.9 | 68.9 |
| `process_prep_regimen_variables` | raw | 5 | 26.8 | 25.8 | 29.4 |
| `process_prophylaxis_drugs` | raw | 5 | 29.8 | 27.9 | 30.1 |
| `process_upset_plot` | raw | 5 | 594.3 | 574.8 | 617.5 |
| `competing_risks_agvhd_100d` | processed | 3 | 996.8 | 994.7 | 1008.3 |
| `km_survival_lifelines` | processed | 5 | 61.8 | 60.7 | 644.0 |
| `json_store_roundtrip` | processed | 5 | 267.5 | 253.2 | 279.4 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
