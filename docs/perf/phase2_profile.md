# Phase 2 — Profilage cProfile

Date : 2026-10-06. Jeu synthétique 16 000 lignes. Top 10 par **temps cumulé** par scénario.

## load_data (parsing CSV + process_data) — total 5264 ms

| Temps cum. (s) | Temps propre (s) | Appels | Fonction |
|---|---|---|---|
| 5.264 | 0.001 | 1 | `load_data` (./modules/data_processing.py:133) |
| 5.177 | 0.011 | 1 | `process_data` (./modules/data_processing.py:274) |
| 2.790 | 0.000 | 3 | `to_datetime` (./.venv/lib/site-packages/pandas/core/tools/datetimes.py:721) |
| 2.789 | 0.000 | 3 | `_convert_listlike_datetimes` (./.venv/lib/site-packages/pandas/core/tools/datetimes.py:369) |
| 2.788 | 0.000 | 3 | `objects_to_datetime64ns` (./.venv/lib/site-packages/pandas/core/arrays/datetimes.py:2306) |
| 2.788 | 0.128 | 3 | `<built-in method pandas._libs.tslib.array_to_datetime>` (~:0) |
| 2.083 | 0.185 | 48000 | `_parse` (./.venv/lib/site-packages/dateutil/parser/_parser.py:666) |
| 1.632 | 0.151 | 1 | `process_prophylaxis_drugs` (./modules/data_processing.py:470) |
| 1.075 | 0.079 | 48000 | `split` (./.venv/lib/site-packages/dateutil/parser/_parser.py:199) |
| 0.958 | 0.081 | 480000 | `__next__` (./.venv/lib/site-packages/dateutil/parser/_parser.py:189) |

## process_data seul — total 6044 ms

| Temps cum. (s) | Temps propre (s) | Appels | Fonction |
|---|---|---|---|
| 6.044 | 0.000 | 1 | `target_process_data` (./scripts/perf/perf_targets.py:83) |
| 6.044 | 0.000 | 1 | `run_quiet` (./scripts/perf/perf_targets.py:75) |
| 6.044 | 0.014 | 1 | `process_data` (./modules/data_processing.py:274) |
| 3.390 | 0.000 | 3 | `to_datetime` (./.venv/lib/site-packages/pandas/core/tools/datetimes.py:721) |
| 3.389 | 0.000 | 3 | `_convert_listlike_datetimes` (./.venv/lib/site-packages/pandas/core/tools/datetimes.py:369) |
| 3.388 | 0.000 | 3 | `objects_to_datetime64ns` (./.venv/lib/site-packages/pandas/core/arrays/datetimes.py:2306) |
| 3.388 | 0.188 | 3 | `<built-in method pandas._libs.tslib.array_to_datetime>` (~:0) |
| 2.506 | 0.230 | 48000 | `_parse` (./.venv/lib/site-packages/dateutil/parser/_parser.py:666) |
| 1.769 | 0.161 | 1 | `process_prophylaxis_drugs` (./modules/data_processing.py:470) |
| 1.274 | 0.092 | 48000 | `split` (./.venv/lib/site-packages/dateutil/parser/_parser.py:199) |

## competing_risks GvH aiguë 100 j — total 2223 ms

| Temps cum. (s) | Temps propre (s) | Appels | Fonction |
|---|---|---|---|
| 2.223 | 0.000 | 1 | `target_competing_risks_agvhd` (./scripts/perf/perf_targets.py:111) |
| 2.216 | 0.005 | 1 | `run_quiet` (./scripts/perf/perf_targets.py:75) |
| 2.212 | 0.198 | 1 | `calculate_cumulative_incidence` (./modules/competing_risks.py:201) |
| 0.617 | 0.016 | 16001 | `iterrows` (./.venv/lib/site-packages/pandas/core/frame.py:1401) |
| 0.535 | 0.069 | 16519 | `__init__` (./.venv/lib/site-packages/pandas/core/series.py:371) |
| 0.494 | 0.123 | 145284 | `__getitem__` (./.venv/lib/site-packages/pandas/core/series.py:1016) |
| 0.463 | 0.003 | 1019 | `__getitem__` (./.venv/lib/site-packages/pandas/core/frame.py:3853) |
| 0.450 | 0.001 | 505 | `_getitem_bool_array` (./.venv/lib/site-packages/pandas/core/frame.py:3921) |
| 0.417 | 0.001 | 496 | `_take_with_is_copy` (./.venv/lib/site-packages/pandas/core/generic.py:4077) |
| 0.413 | 0.002 | 496 | `take` (./.venv/lib/site-packages/pandas/core/generic.py:3962) |

## json_store_roundtrip (H4) — total 327 ms

| Temps cum. (s) | Temps propre (s) | Appels | Fonction |
|---|---|---|---|
| 0.327 | 0.042 | 1 | `target_json_roundtrip` (./scripts/perf/perf_targets.py:133) |
| 0.220 | 0.000 | 1 | `read_json` (./.venv/lib/site-packages/pandas/io/json/_json.py:500) |
| 0.214 | 0.000 | 1 | `read` (./.venv/lib/site-packages/pandas/io/json/_json.py:980) |
| 0.214 | 0.000 | 1 | `_get_object_parser` (./.venv/lib/site-packages/pandas/io/json/_json.py:1022) |
| 0.214 | 0.006 | 1 | `parse` (./.venv/lib/site-packages/pandas/io/json/_json.py:1172) |
| 0.120 | 0.003 | 1 | `_parse` (./.venv/lib/site-packages/pandas/io/json/_json.py:1360) |
| 0.087 | 0.000 | 2 | `__init__` (./.venv/lib/site-packages/pandas/core/frame.py:665) |
| 0.087 | 0.004 | 1 | `_try_convert_types` (./.venv/lib/site-packages/pandas/io/json/_json.py:1422) |
| 0.082 | 0.000 | 2 | `_process_converter` (./.venv/lib/site-packages/pandas/io/json/_json.py:1396) |
| 0.073 | 0.009 | 2 | `arrays_to_mgr` (./.venv/lib/site-packages/pandas/core/internals/construction.py:96) |

## plotly create_barplot — total 398 ms

| Temps cum. (s) | Temps propre (s) | Appels | Fonction |
|---|---|---|---|
| 0.398 | 0.000 | 1 | `scenario_plotly_barplot` (./scripts/perf/profile_compute.py:36) |
| 0.396 | 0.000 | 1 | `create_barplot` (./visualizations/allogreffes/graphs.py:311) |
| 0.364 | 0.001 | 289 | `__setitem__` (./.venv/lib/site-packages/plotly/basedatatypes.py:4813) |
| 0.364 | 0.000 | 2 | `update_layout` (./.venv/lib/site-packages/plotly/graph_objs/_figure.py:749) |
| 0.364 | 0.000 | 2 | `update_layout` (./.venv/lib/site-packages/plotly/basedatatypes.py:1369) |
| 0.364 | 0.000 | 2 | `update` (./.venv/lib/site-packages/plotly/basedatatypes.py:5112) |
| 0.363 | 0.000 | 4 | `_perform_update` (./.venv/lib/site-packages/plotly/basedatatypes.py:3854) |
| 0.362 | 0.003 | 919 | `_find_and_load` (<frozen importlib._bootstrap>:1022) |
| 0.359 | 0.001 | 907 | `import_module` (C:/Users/axelz/AppData/Local/Programs/Python/Python310/lib/importlib/__init__.py:108) |
| 0.357 | 0.001 | 908 | `_gcd_import` (<frozen importlib._bootstrap>:1038) |

## Synthèse des coûts

| Scénario | Total (ms) |
|---|---|
| load_data (parsing CSV + process_data) | 5264 |
| process_data seul | 6044 |
| competing_risks GvH aiguë 100 j | 2223 |
| json_store_roundtrip (H4) | 327 |
| plotly create_barplot | 398 |

---

## Verdict (rédigé)

- **H2 (iterrows) : confirmée mais n'est PAS le premier goulot du chargement.** Dans `process_data` (6,0 s sous profileur / 1,8 s réel), le premier coût est **`pd.to_datetime(..., format='mixed')`** : 2,9 s cumulés sous profileur, dont 2,2 s dans le parseur `dateutil` appelé **élément par élément** (48 000 appels de `_parse` pour 3 colonnes × 16 000 lignes). `format='mixed'` désactive le chemin vectorisé de pandas. Viennent ensuite `process_prophylaxis_drugs` (1,7 s profilé / 0,5 s réel, `iterrows`).
- **`calculate_cumulative_incidence`** (2,1 s profilé / 0,9 s réel) : `iterrows` (0,56 s) + construction d'une Series par ligne (16 519 `Series.__init__`) + balayages booléens du DataFrame pour chacun des 101 jours. Vectorisable intégralement.
- **H4 (JSON) : confirmée, coût modéré côté serveur** (249 ms profilés pour 14,5 Mo) mais **coût réseau dominant côté nginx** (phase 1 : 38 callbacks renvoient le dataset complet). Le levier principal est de réduire le volume (phase 4), pas d'accélérer le parsing.
- **Figures Plotly** : 398 ms profilés pour un barplot simple, dominés par la validation des propriétés `update_layout` (overhead Plotly connu, non compressible sans changer les graphiques). Non prioritaire.
- Lecture CSV (`load_data` vs `process_data`) : ~0,1–0,2 s — négligeable.

### Ordre de priorité pour la phase 3

1. Parsing des dates : format explicite rapide + repli `mixed` (équivalence garantie par golden master).
2. `process_prophylaxis_drugs` et `process_upset_plot` : vectorisation du pivot médicaments × patients.
3. `calculate_cumulative_incidence` : vectorisation de l'affectation événement/temps par patient et des comptages par jour.
