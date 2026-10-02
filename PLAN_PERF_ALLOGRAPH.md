# AlloGraph : plan d'optimisation des performances (brief pour agents IA)

> À placer à la racine du dépôt. La section « Contraintes » peut aussi être copiée dans le fichier d'instructions de ton agent (`.github/copilot-instructions.md`, `CLAUDE.md` ou `AGENTS.md`) pour qu'elle s'applique à chaque session.

## 1. Contexte

- Application Dash de visualisation de données patients (greffes) : analyses de prophylaxie, risques compétitifs, Kaplan-Meier.
- Stack : Python, Dash, pandas, Flask ; déployée avec gunicorn (4 workers) derrière nginx, sur une VM de 4 vCPU et 7,8 Go de RAM, elle-même derrière un frontal de l'université qui gère le HTTPS.
- Le site est public et manipule des données de santé. Objectif de conception : **rien de persistant côté serveur** (éviter les contraintes HDS). Les données vivent uniquement dans le navigateur de l'utilisateur (`dcc.Store`).

## 2. Contraintes non négociables

1. **Aucune donnée patient conservée côté serveur** : pas de cache fichier (`flask_caching` filesystem interdit), pas de dictionnaire global ou de mémoïsation en RAM contenant des données, pas d'écriture disque de données, pas de base de données.
2. **Pas d'état global sur `app.server`** ni dans des variables de module : les 4 workers gunicorn ont chacun leur mémoire, ce qui rend le comportement non déterministe et peut mélanger des données entre utilisateurs.
3. Tous les `dcc.Store` contenant des données patient utilisent `storage_type="memory"` (jamais `local` ni `session`).
4. Aucune donnée patient dans les logs, les messages d'erreur ou les exceptions affichées.
5. Aucun appel réseau sortant, aucune nouvelle dépendance sans validation explicite.
6. **Ne jamais utiliser de vraies données patient** pour développer, tester ou dans un prompt. Utiliser uniquement un jeu de données synthétique de même schéma (voir phase 0).
7. Le comportement fonctionnel doit rester **strictement identique** : mêmes résultats numériques, mêmes graphiques.
8. Travail sur une branche dédiée. Aucune modification de la production ni de la configuration nginx/gunicorn (les changements d'infrastructure sont seulement proposés, pas appliqués).

## 3. Mesures déjà relevées (faits)

- Calcul isolé (risques compétitifs) : un seul worker gunicorn à ~100 % d'un cœur, les 3 autres au repos. Un traitement Python tient sur un cœur (GIL).
- Navigation entre onglets avec ~16 000 lignes chargées : les 4 workers montent à 40-100 % ; nginx monte à ~19 % ; ~20 requêtes `_dash-update-component` par changement d'onglet.
- Pas de steal CPU, pas de pression mémoire, pas de swap. L'infrastructure n'est pas le goulot actuel.
- Les réponses des requêtes Dash sont petites (0,4 à 50 ko).
- **Mesure clé : une requête `_dash-update-component` prise au hasard envoie ~57 Mo (Content-Length 56 838 304) au serveur** avec ~16 000 lignes chargées. Les requêtes ne sont pas compressées par le navigateur. H1 est donc très probablement confirmée ; reste à mesurer combien des ~20 requêtes sont dans ce cas (voir phase 1).

## 4. Hypothèses à vérifier (ne pas les considérer comme acquises)

- **H1** : plusieurs callbacks reçoivent le `dcc.Store` complet (16 000 lignes en JSON) en `Input` ou `State`, donc le renvoient et le redécodent à chaque appel.
- **H2** : des `iterrows()` (notamment `process_prophylaxis_drugs` dans `data_processing.py`, et `competing_risks.py`) dominent le temps de calcul.
- **H3** : un changement d'onglet déclenche une cascade de callbacks redondants qui refont le même travail.
- **H4** : la sérialisation JSON/désérialisation du DataFrame représente une part notable du coût.

## 5. Règles de travail pour l'agent

- **Mesurer avant de modifier**, et remesurer après. Aucune optimisation sans chiffre avant/après.
- Un changement à la fois, un commit par changement, avec les mesures dans le message de commit.
- Tout remplacement de code doit être couvert par un test d'équivalence (voir phase 3).
- Ne pas refactorer au-delà du périmètre de la phase en cours. Ne rien « améliorer » au passage.
- En cas d'ambiguïté (comportement attendu, schéma de données), poser la question au lieu de supposer.
- Chaque phase se termine par un court rapport dans `docs/perf/` : ce qui a été mesuré, ce qui a été changé, les chiffres.

## 6. Phases

### Phase 0 : Base de mesure et filet de sécurité (aucun changement de code applicatif)

*Pourquoi : sans jeu de données reproductible et sans résultats de référence, on ne peut ni mesurer un gain ni prouver qu'on n'a rien cassé.*

1. Écrire un script qui génère un jeu de données **synthétique** (~16 000 lignes, même schéma, mêmes types et même distribution approximative que le vrai fichier, graine aléatoire fixe). Lui, et seulement lui, sert pour tous les tests.
2. Isoler les fonctions de calcul pures (celles qui prennent un DataFrame et renvoient un résultat) et enregistrer leurs sorties sur ce jeu comme **résultats de référence** (« golden master », dans `tests/`).
3. Écrire un script de benchmark qui chronomètre chaque fonction (`time.perf_counter`, plusieurs répétitions, médiane).
4. Livrable : tableau des temps de référence par fonction.

### Phase 1 : Inventaire des callbacks (lecture seule)

*Pourquoi : 20 requêtes pour un changement d'onglet indiquent des cascades. Il faut une carte avant de couper.*

1. Lister tous les callbacks : fonction, `Input`, `State`, `Output`, usage de `dcc.Store`, `prevent_initial_call`.
2. Pour chacun, indiquer s'il reçoit le Store complet, et s'il fait un calcul lourd ou seulement un affichage.
3. Repérer : callbacks redondants, callbacks qui se déclenchent en cascade, `Input` qui pourraient être des `State`.
4. Livrable : tableau + graphe de dépendances (Mermaid) dans `docs/perf/callbacks.md`.

*(À faire en parallèle par toi : lancer l'appli en local avec `app.run(debug=True)` et relever, dans le panneau « Callbacks » des outils de développement Dash, la durée et la taille de chaque callback.)*

### Phase 2 : Profilage (aucun changement de code applicatif)

1. Profiler les fonctions de calcul sur le jeu synthétique avec `cProfile` (tri par temps cumulé) ou `pyinstrument`.
2. Séparer le coût de : lecture/parsing du fichier, traitements pandas, sérialisation JSON du Store, construction des figures Plotly.
3. Livrable : top 10 des fonctions par temps cumulé, et verdict sur H2 et H4.

### Phase 3 : Vectoriser les points chauds

*Pourquoi : sur 16 000 lignes, un traitement vectorisé prend des dizaines de millisecondes, contre plusieurs secondes pour `iterrows()` qui crée un objet Python par ligne. C'est le plus gros gain et il ne conserve rien côté serveur.*

1. Réécrire les `iterrows()` identifiés en phase 2 (opérations pandas vectorisées, `groupby`, `merge`, `np.where`, etc.).
2. Pour chaque fonction réécrite : test d'équivalence avec `pd.testing.assert_frame_equal` (ou comparaison numérique avec tolérance) contre les résultats de référence de la phase 0.
3. Re-benchmark. Livrable : avant/après par fonction.

### Phase 4 : Réduire le travail et le volume échangé

*Pourquoi : même rapide, un traitement refait 20 fois est du gaspillage. On réduit la quantité de données et de callbacks, sans cache serveur.*

1. Calculer **une fois** toutes les agrégations nécessaires aux onglets, au chargement du fichier, et ne stocker dans le `dcc.Store` que ces agrégats (quelques centaines de valeurs) quand les onglets n'ont pas besoin des lignes brutes.
2. Quand les lignes brutes sont indispensables : colonnes inutiles supprimées, types `category`/entiers compacts, sérialisation `orient="split"`.
3. Transformer en `State` les `Input` qui n'ont pas besoin de redéclencher le callback ; fusionner les callbacks redondants.
4. Évaluer les **clientside callbacks** pour les parties simples (tracé à partir d'agrégats, filtres légers) : exécutées dans le navigateur, elles ne chargent pas le serveur et ne font transiter aucune donnée.
5. Livrable : nombre de requêtes par changement d'onglet et taille des requêtes, avant/après.

### Phase 5 : Revue de la configuration gunicorn (proposition uniquement)

1. Relire la config actuelle (nombre de workers, `--timeout`, `--threads`).
2. Rappel : les threads n'accélèrent pas du calcul Python pur (GIL). Vérifier que le timeout (30 s par défaut) ne tue pas un worker pendant un calcul long.
3. Livrable : recommandations écrites, **sans modifier** la config de production.

### Phase 6 : Audit de conformité (support de l'argumentaire pour la direction)

1. Rechercher dans tout le code : attributs `app.server.*`, variables globales mutables, caches (`lru_cache`, `flask_caching`, dictionnaires de module), écritures disque, `logging` pouvant contenir des données.
2. Vérifier le `storage_type` de chaque `dcc.Store`.
3. **Revue côté nginx (point critique)** : par défaut, nginx met en mémoire tampon le corps des requêtes ; au-delà de `client_body_buffer_size` (quelques ko), il l'écrit dans un **fichier temporaire sur disque** (`client_body_temp_path`) avant de le transmettre à gunicorn. Avec des requêtes de plusieurs dizaines de Mo contenant des données patient, cela contredit l'argument « rien sur le disque du serveur ». Vérifier `client_body_buffer_size`, `client_body_temp_path`, `proxy_request_buffering` et `client_max_body_size` dans la config nginx, puis proposer une correction (la meilleure : réduire les requêtes à quelques ko, ce qui rend le problème sans objet).
4. Livrable : rapport daté listant les constats et confirmant l'absence de persistance côté serveur.

## 7. Critères de réussite (à fixer avec toi avant la phase 3)

- Temps des fonctions de calcul (médiane) avant/après, sur le jeu synthétique.
- Nombre et taille des requêtes `_dash-update-component` par changement d'onglet.
- CPU gunicorn pendant une navigation type : pas de saturation des 4 cœurs pour un seul utilisateur.
- Résultats numériques identiques aux références (tests verts).
- Zéro nouvelle persistance côté serveur (phase 6 propre).

## 8. Prompt de démarrage à coller dans l'agent

```text
Tu travailles sur AlloGraph, une application Dash qui manipule des données de santé.
Lis intégralement PLAN_PERF_ALLOGRAPH.md à la racine du dépôt, en particulier la section
« Contraintes non négociables » : elle prime sur toute autre considération.

Commence par la phase 0 uniquement, puis arrête-toi et fais-moi un rapport :
1. Crée un générateur de jeu de données SYNTHÉTIQUE (~16 000 lignes) à partir du schéma
   que tu déduis du code. N'utilise jamais de vraies données patient.
2. Identifie les fonctions de calcul pures et enregistre leurs sorties de référence
   dans tests/.
3. Écris un script de benchmark et donne-moi le tableau des temps.
Ne modifie aucun code applicatif. Si le schéma des données est ambigu, pose-moi la question.
Ensuite j'attendrai ton rapport avant de te demander de passer à la phase suivante.
```
