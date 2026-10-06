# Phase 0 — temps de référence des fonctions pures

Date : 2026-10-06 — jeu synthétique 16000 lignes (graine fixe).
Machine : poste de développement (Windows). Médiane sur N répétitions, `time.perf_counter`.

| Fonction | Entrée | Rép. | Médiane (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|
| `process_data` | raw | 5 | 895.6 | 862.7 | 899.7 |
| `create_greffes_variable` | raw | 5 | 60.9 | 60.7 | 64.0 |
| `create_blood_rh_variable` | raw | 5 | 64.0 | 63.2 | 65.4 |
| `create_hla_compatibility_variable` | raw | 5 | 63.1 | 61.0 | 65.3 |
| `process_prep_regimen_variables` | raw | 5 | 25.0 | 23.9 | 25.4 |
| `process_prophylaxis_drugs` | raw | 5 | 497.8 | 490.9 | 508.9 |
| `process_upset_plot` | raw | 5 | 578.8 | 563.6 | 614.0 |
| `competing_risks_agvhd_100d` | processed | 3 | 1102.9 | 923.8 | 1260.0 |
| `km_survival_lifelines` | processed | 5 | 60.6 | 58.7 | 643.5 |
| `json_store_roundtrip` | processed | 5 | 247.1 | 243.5 | 259.4 |

Taille de la sérialisation JSON `orient='split'` du DataFrame traité : 14.5 Mo (hypothèse H4).
