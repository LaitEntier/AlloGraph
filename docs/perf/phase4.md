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

## Mesures avant/après (16 000 lignes synthétiques)

| Store | Avant (records) | Après (codec) | Ratio |
|---|---|---|---|
| `data-store` (complet) | 43,8 Mo | 7,1 Mo | **6,1×** |
| `data-store-survival` | 8,8 Mo | 1,9 Mo | 4,5× |
| `data-store-gvh` | 8,0 Mo | 1,8 Mo | 4,5× |
| `data-store-viz` | 11,8 Mo | 1,5 Mo | 7,7× |
| navigation / sidebars | 43,8 Mo | ~0,3 ko | — |

Coût CPU par callback (médiane, machine de dev) :

| Opération | Avant | Après |
|---|---|---|
| Décodage du store complet | 99 ms (`pd.DataFrame(records)`) | 88 ms |
| Encodage à l'upload (une fois) | — | ~1,3 s |

Requêtes par changement d'onglet : les callbacks de navigation/sidebar/purge ne transportent plus de données patient ; seuls les callbacks de la page active envoient leur store (1,5–7,1 Mo au lieu de 43,8). **À re-mesurer dans les devtools Dash en conditions réelles.**

## Points du plan évalués et écartés

- **Agrégats pré-calculés au chargement (item 1)** : écarté. Les onglets appliquent des filtres dynamiques (année, âge, diagnostic) et affichent des données ligne à ligne (boxplots, datatables de données manquantes, courbes KM/risques compétitifs) : l'agrégat pré-calculé ne peut pas remplacer les lignes. Le codec + stores slim apportent l'essentiel du gain sans figer les agrégations.
- **Clientside callbacks (item 4)** : écarté pour l'instant. Après la phase 3, les calculs serveur sont de l'ordre de 30–90 ms ; le coût dominant était le transfert (résolu par le codec). Réévaluer si les mesures réelles montrent un calcul > 500 ms.
- **Stores par page dédiés** : écarté (risque/récompense défavorable). Déduire statiquement les colonnes de chaque page risque d'omettre une colonne utilisée via un garde-fou `'Col' in df.columns`, ce qui changerait silencieusement les résultats. Les slim stores existants (survival/gvh/viz) couvrent déjà les pages les plus lourdes.

## Vérifications

- Tests : **10 passed** (4 golden masters + 6 codec) après chaque commit.
- `import app` OK (Dash valide les signatures de callbacks au chargement).
- Comportement fonctionnel : équivalence du codec prouvée par test ; aucun calcul modifié dans cette phase.
- Conformité : aucune persistance serveur ajoutée ; tous les stores restent en `memory`.

## Reste à faire (validation terrain)

- Relevé devtools Dash (panneau Callbacks) : nombre et taille des requêtes par changement d'onglet, avant/après déploiement.
- Surveiller le temps d'upload (ajout ~1,5–2 s d'encodage sur 16k lignes, une fois par chargement).
