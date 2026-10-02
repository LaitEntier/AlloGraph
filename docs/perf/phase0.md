# Phase 0 — Base de mesure et filet de sécurité

Date : 2026-10-03. Branche : `perf/phase-0-baseline`. **Aucun code applicatif modifié.**

## Ce qui a été créé

| Fichier | Rôle |
|---|---|
| `scripts/perf/synthetic_data.py` | Générateur du jeu synthétique (16 000 lignes, 66 colonnes au schéma EBMT, graine fixe 42, reproductible en ~0,5 s). CLI : `python scripts/perf/synthetic_data.py [n] [csv]`. |
| `scripts/perf/perf_targets.py` | Registre des fonctions pures mesurées/figées (partagé par capture, benchmark et tests). |
| `scripts/perf/capture_golden.py` | Capture des sorties de référence dans `tests/golden/*.pkl.gz` + `manifest.json`. |
| `scripts/perf/benchmark.py` | Benchmark (`time.perf_counter`, médiane) → régénère `docs/perf/phase0_benchmark.md`. |
| `tests/test_golden_master.py` | 4 tests d'équivalence contre les golden masters (filet de sécurité pour la phase 3). |

Le CSV généré (`data/synthetic_16k.csv`, 9,4 Mo) est ignoré par git : il se régénère à l'identique. Aucune donnée patient réelle utilisée ; les distributions sont des approximations déduites du schéma attendu par `modules/data_processing.py` et de métadonnées agrégées de l'échantillon de test dés-identifié du dépôt.

## Données synthétiques

- 16 000 lignes, schéma strictement identique (66 colonnes `EXPECTED_COLUMNS`), dates au format `dd/mm/yyyy HH:MM`.
- Cohérence interne : naissance ≤ diagnostic ≤ greffe (2018–2024) ≤ événements ≤ dernier suivi ; ~27 % de décès, ~47 % de GvH aiguë, ~23 % de GvH chronique, ~17 % de rechutes ; prophylaxie tirée par schémas combinés réalistes (incluant les libellés qui déclenchent les mappings ATG/ALTG).

## Temps de référence (médiane, 16 000 lignes)

| Fonction | Médiane |
|---|---|
| `process_data` (pipeline complet au chargement) | **1 798 ms** |
| dont `process_prophylaxis_drugs` (`iterrows`) | 505 ms |
| `process_upset_plot` (`iterrows`) | 564 ms |
| `competing_risks_agvhd_100d` (`iterrows` + balayages par jour) | **923 ms** |
| `create_greffes_variable` / `create_blood_rh_variable` / `create_hla_compatibility_variable` (`apply` ligne) | ~60 ms chacune |
| `process_prep_regimen_variables` | 25 ms |
| `km_survival_lifelines` (Kaplan-Meier global) | 59 ms |
| Aller-retour JSON du DataFrame traité (H4) | 233 ms pour **14,5 Mo** |

Détail dans `docs/perf/phase0_benchmark.md`.

## Constats

- **H2 (iterrows) étayée** : les trois boucles Python sur les lignes (`process_prophylaxis_drugs`, `process_upset_plot`, `calculate_cumulative_incidence`) totalisent ~2,0 s à elles seules sur 16 000 lignes — cibles prioritaires de la phase 3.
- **H4 (sérialisation) quantifiée** : le DataFrame traité fait 14,5 Mo en JSON `split` et ~233 ms par aller-retour. Cohérent avec les ~57 Mo observés en requête (plusieurs stores + payload Dash complet). À recouper avec l'inventaire des callbacks (phase 1).
- Les `apply` ligne par ligne de `data_processing.py` (~180 ms cumulés) sont des cibles secondaires faciles.
- Aucun `datetime.now()` dans les fonctions de calcul pures (seulement pour nommer des fichiers d'export) : les golden masters sont reproductibles.

## Points signalés pour les phases suivantes

- `modules/competing_risks.py` (lignes 286–292) imprime des lignes de debug par patient (`print(f"Patient {idx}: ...")`) : coût inutile et fuite potentielle d'identifiants dans les logs — à traiter (phase 3/6).
- `calculate_cumulative_incidence` refait un balayage complet du DataFrame pour chaque jour (101 jours × 16 000 lignes) : vectorisation directe possible.
- `docs/perf/phase0_benchmark.md` note `km_survival_lifelines` max=614 ms : premier appel lifelines (compilation/imports) ; la médiane est représentative.

## Vérification

- `python -m pytest tests/ -q` → **4 passed** (les golden masters correspondent au code actuel).
- Aucune modification applicative ; seuls des ajouts (scripts, tests, docs) + `.gitignore` (exclusion du CSV régénérable).
