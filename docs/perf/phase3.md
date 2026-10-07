# Phase 3 — Vectorisation des points chauds

Date : 2026-10-06. Branche : `perf/phase-0-baseline`. 5 commits, un par changement, tests golden masters verts après chacun.

## Avant / après (médiane, jeu synthétique 16 000 lignes)

| Fonction | Phase 0 (ms) | Phase 3 (ms) | Gain |
|---|---|---|---|
| `process_data` (pipeline complet) | 1 798 | **213** | −88 % |
| dont parsing des 3 colonnes de dates | ~800 (est. profilage) | ~10 | format explicite + repli `mixed` |
| `process_prophylaxis_drugs` (`iterrows`) | 505 | **29** | −94 % |
| `process_upset_plot` (`iterrows`) | 564 | **29** | −95 % |
| `calculate_cumulative_incidence` GvH aiguë 100 j | 923 | **83** | −91 % |
| `create_greffes_variable` (`apply` ligne) | 64 | 8 | −87 % |
| `create_blood_rh_variable` (`apply` ligne) | 63 | 13 | −79 % |
| `create_hla_compatibility_variable` (`apply` ligne) | 62 | 24 | −61 % |
| `km_survival_lifelines` | 59 | 58 | inchangé (non touché) |
| Aller-retour JSON du Store | 233 | 259 | inchangé (cible phase 4) |

## Changements (un commit chacun)

1. **`220c713` — parsing des dates** : `_to_datetime_fast` (format explicite `%d/%m/%Y %H:%M` puis repli `mixed` sur les valeurs non reconnues). `process_data` : 1 798 → 896 ms.
2. **`7e8c108` — `process_prophylaxis_drugs`** : pivot long/large des 6 colonnes + mapping sur valeurs uniques (suppression de l'`iterrows`). 896 → 417 ms pour `process_data`.
3. **`5e69905` — `process_upset_plot`** : même pivot (sortie 0/1). 564 → 29 ms.
4. **`ed37da5` — `calculate_cumulative_incidence`** : affectation événement/temps vectorisée, comptages par jour vectorisés, suppression des prints de debug par patient. 923 → 83 ms. **Changement comportemental validé par l'utilisateur** (voir ci-dessous).
5. **`ed9749d` — `apply` ligne de `data_processing`** : `create_greffes_variable`, `create_blood_rh_variable`, `create_hla_compatibility_variable`, `process_prep_regimen_variables`. `process_data` : 417 → 213 ms.

## Preuve d'équivalence

- Golden masters (phase 0) : 4 tests `assert_frame_equal` sur `process_data`, `process_upset_plot`, `competing_risks_agvhd_100d`, `km_survival_lifelines` — **verts après chaque commit**.
- Pour `calculate_cumulative_incidence`, vérification supplémentaire : la boucle `iterrows` d'origine a été instrumentée (copie du fichier avec `dayfirst=True` ajouté) et comparée à la version vectorisée sur les 16 000 lignes : `results_df`, `event_type` et `event_time` **strictement identiques**, y compris les règles de départage (ordre de config, décès en dernier, égalités de temps).

## Changement comportemental assumé (validé par l'utilisateur)

`competing_risks.py` parsait les dates d'événements **sans `dayfirst`** : les dates ambiguës (jour ≤ 12) étaient lues mois-d'abord (`09/04/2021` → 4 septembre) alors que `process_data` lit jour-d'abord partout. C'était très probablement un bug latent affectant les analyses GvH/rechute en production. Décision : **corriger en jour-d'abord** (commit `ed37da5`). Le golden master `competing_risks_agvhd_100d` a été régénéré et documente le nouveau comportement de référence. **Les chiffres des pages GvH/Relapse/Toxicity peuvent donc différer légèrement de la production actuelle sur les dates ambiguës.**

Autre changement volontaire : les `print` de debug par patient (qui exposaient des identifiants de lignes dans les logs) ont été supprimés de `calculate_cumulative_incidence` — cohérent avec la contrainte 4 du plan.

## Reste pour la phase 4

Le calcul n'est plus le goulot principal (0,2–0,4 s au chargement, 83 ms par risque compétitif). Le coût dominant est désormais le **volume échangé** (H1/H4 : 38 callbacks qui reçoivent le dataset complet en `Input`, 14,5 Mo par store sérialisé) : agrégats au chargement, slim stores généralisés, `Input` → `State`, éventuels clientside callbacks.
