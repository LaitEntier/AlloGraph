# Phase 4 — Réduction du volume échangé et du travail redondant

Date : 2025 (branche `perf/phase-0-baseline`). Jeu de mesure : données **synthétiques** 16 000 lignes (`scripts/perf/synthetic_data.py`, graine 42).

## Contexte (mesures initiales, avant phase 4)

- `data-store` complet en format `records` : **43,8 Mo** JSON côté navigateur.
- Chaque callback ayant `Input('data-store')` renvoyait ce volume au serveur (mesure production : ~57 Mo pour une requête `_dash-update-component`).
- ~20 requêtes par changement d'onglet, dont la navigation elle-même (qui n'utilisait les données que pour tester `data is None`).
- L'upload déclenchait un **second aller-retour** : `data-store` → serveur → 3 slim stores (`update_slim_stores`).

## Changements

### 4.1 — Navigation et sidebars sans données patient (commit `5f2fc1a`)

- Nouveau `metadata-store` léger : `{original_shape, processed_shape, filename, years, n_patients}` (~0,3 ko).
- `navigate`, `update_sidebar`, `toggle_sidebar_visibility`, `toggle_purge_button_visibility` ne reçoivent plus `data-store`.
- Les 6 fonctions de sidebar (GvH, Relapse, Toxicity, Survival, Indicators, Procedures) utilisent `metadata['years']` / `metadata['n_patients']` au lieu de reconstruire un DataFrame complet pour 3 valeurs.
- Suppression d'une branche `Patients` dupliquée (morte) dans `update_sidebar`.

### 4.2 — Codec compact pour les stores (commit `24f16d3`)

`modules/data_processing.py` :

- `df_to_store_payload(df, columns=None)` : orientation `split` (noms de colonnes une seule fois), codebook entier pour les colonnes texte répétitives (cardinalité ≤ 50 % des lignes), dates en ISO 8601.
- `store_payload_to_df(payload)` : reconstruction équivalente à `pd.DataFrame(records)` (None pour les manquants, dates en chaînes ISO re-parsées par les pages).
- `tests/test_store_codec.py` : équivalence avec l'ancien chemin de sérialisation (`to_dict('records')` + `PlotlyJSONEncoder`) vérifiée par `assert_frame_equal` sur le jeu synthétique traité.

### 4.3+4.4 — Codec partout, slim stores calculés à l'upload (commit `f05e824`)

- Les callbacks d'upload (`process_uploaded_file`, `load_test_sample`) sérialisent `data-store` **et** les 3 slim stores en une seule passe.
- Suppression du callback `update_slim_stores` (aller-retour de 43,8 Mo évité à chaque chargement).
- Les 9 pages décodent via `store_payload_to_df` (43 sites).
- Page GvH : les 3 callbacks restants sur le store complet basculent sur `data-store-gvh` (colonnes vérifiées suffisantes).
- Décodage codebook vectorisé numpy (commit `ba33766`) : 380 → 88 ms.

### 4.6 — Stores allégés par page (commit `80f1461`)

- 6 nouveaux stores dédiés : `data-store-home` (0,08 Mo), `-hemopathies` (1,15), `-procedures` (3,83), `-relapse` (1,40), `-toxicity` (1,40), `-indics` (2,42), contre 7,1 Mo pour le store complet.
- Patients utilise `data-store-viz` (1,52 Mo) pour tous ses callbacks, Survival `data-store-survival` (1,94), GvH `data-store-gvh` (1,76).
- **Plus aucun callback de page n'utilise le store complet** (test de régression `test_no_page_callback_uses_full_store`).
- Page Procedures : les colonnes de prophylaxie, détectées dynamiquement par scan Oui/Non dans le callback, sont incluses au chargement en appliquant la même règle.
- Sécurité contre les omissions silencieuses (`'Col' in df.columns`) : `tests/test_page_stores.py` exécute chaque callback avec le store complet puis le store de page (2 combos de filtres) et compare les sorties sérialisées.

### 4.7 — Fusion des callbacks à Inputs identiques (commits `dd1de3c`, `296af30`, `295085e`)

Inventaire via `app.callback_map` : 8 groupes de callbacks (15 callbacks) partageaient strictement les mêmes Inputs → fusionnés en 8 callbacks (une requête au lieu de 2-3 par changement de filtre) : relapse (3→1), toxicity (3→1), patients (2→1), hemopathies (2→1), gvh manquants (2→1), survival courbes (2→1), survival manquants (2→1), indicators manquants (2→1).

Équivalence prouvée : sorties sérialisées capturées **avant** fusion (`tests/golden/callback_outputs.json.gz`), comparées après fusion dans `tests/test_merged_callbacks.py`.

## Mesures avant/après (16 000 lignes synthétiques)

| Store | Avant (records) | Après (codec) | Ratio |
|---|---|---|---|
| `data-store` (complet) | 43,8 Mo | 7,1 Mo | **6,1×** |
| `data-store-survival` | 8,8 Mo | 1,9 Mo | 4,5× |
| `data-store-gvh` | 8,0 Mo | 1,8 Mo | 4,5× |
| `data-store-viz` | 11,8 Mo | 1,5 Mo | 7,7× |
| navigation / sidebars | 43,8 Mo | ~0,3 ko | — |

Volume par requête de callback selon la page (avant : 43,8 Mo partout) :

| Page | Store utilisé | Taille |
|---|---|---|
| Home | `data-store-home` | 0,08 Mo |
| Patients | `data-store-viz` | 1,5 Mo |
| Indications | `data-store-hemopathies` | 1,2 Mo |
| Procedures | `data-store-procedures` | 3,8 Mo |
| GvH | `data-store-gvh` | 1,8 Mo |
| Relapse / Toxicity | stores dédiés | 1,4 Mo |
| Survival | `data-store-survival` | 1,9 Mo |
| Indicators | `data-store-indics` | 2,4 Mo |

Requêtes par changement de filtre : réduites par les fusions (ex. Relapse : 3 → 1 ; Survival : 4 → 2). Navigation/sidebar/purge : ~0,3 ko. **À re-mesurer dans les devtools en conditions réelles.**

Coût CPU par callback (médiane, machine de dev) :

| Opération | Avant | Après |
|---|---|---|
| Décodage du store complet | 99 ms (`pd.DataFrame(records)`) | 88 ms |
| Encodage à l'upload (une fois) | — | ~1,3 s |

Requêtes par changement d'onglet : les callbacks de navigation/sidebar/purge ne transportent plus de données patient ; seuls les callbacks de la page active envoient leur store (1,5–7,1 Mo au lieu de 43,8). **À re-mesurer dans les devtools Dash en conditions réelles.**

## Points du plan évalués et écartés

- **Agrégats pré-calculés au chargement (item 1)** : écarté. Les onglets appliquent des filtres dynamiques (année, âge, diagnostic) et affichent des données ligne à ligne (boxplots, datatables de données manquantes, courbes KM/risques compétitifs) : l'agrégat pré-calculé ne peut pas remplacer les lignes. Le codec + stores par page apportent l'essentiel du gain sans figer les agrégations.
- **Clientside callbacks (item 4)** : écarté pour l'instant. Après la phase 3, les calculs serveur sont de l'ordre de 30–90 ms ; le coût dominant était le transfert (résolu par le codec + stores par page). Réévaluer si les mesures réelles montrent un calcul > 500 ms.
- **Stores par page** : implémenté (4.6) avec harnais d'équivalence, contrairement à l'estimation initiale de risque — le risque d'omission de colonne est couvert par `tests/test_page_stores.py`.

## Vérifications

- Tests : **28 passed** (4 golden masters + 6 codec + 10 stores par page + 8 callbacks fusionnés) après chaque commit.
- `import app` OK (Dash valide les signatures de callbacks au chargement).
- Comportement fonctionnel : équivalence du codec et des fusions prouvée par tests ; calculs inchangés (phase 3).
- Conformité : aucune persistance serveur ajoutée ; tous les stores restent en `memory`.

## Reste à faire (validation terrain)

- Relevé devtools Dash (panneau Callbacks) : nombre et taille des requêtes par changement d'onglet, avant/après déploiement.
- Surveiller le temps d'upload (ajout ~1,5–2 s d'encodage sur 16k lignes, une fois par chargement).
