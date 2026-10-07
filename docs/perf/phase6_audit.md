# Phase 6 — Audit de conformité « rien de persistant côté serveur »

Date : 2026-10-06. Branche : `perf/phase-0-baseline` (inclut les phases 0–3).

## Synthèse

| # | Point | Statut |
|---|---|---|
| 1 | Cache en RAM contenant des données patient (`modules/cache_utils.py`) | **NON CONFORME — à corriger** |
| 2 | `storage_type` des `dcc.Store` | Conforme (`memory` partout) |
| 3 | Écritures disque de données patient | Aucune trouvée |
| 4 | État global sur `app.server` / variables de module | Aucun, hors cache_utils (point 1) |
| 5 | Données patient dans les logs | Corrigé en phase 3 (voir détail) |
| 6 | nginx (bufferisation des corps de requêtes) | À vérifier côté infra (hors dépôt) |

## 1. `modules/cache_utils.py` — constat critique

Le module maintient des **dictionnaires de module en RAM** (`_cache_store`, et un `func_cache` par fonction décorée), persistants **au-delà du cycle requête** et **partagés entre tous les utilisateurs d'un même worker gunicorn**. Utilisé dans `pages/survival.py` (4 fonctions) et `pages/gvh.py` (1 fonction).

Trois problèmes distincts :

1. **Violation des contraintes 1 et 2** : les résultats mis en cache (figures Kaplan-Meier, risques compétitifs — données dérivées de patients) vivent en RAM serveur entre les requêtes, et le comportement devient non déterministe entre les 4 workers. Le docstring affirme « session-scoped : data only lives for the HTTP request/response cycle » — **c'est faux** : le cache survit jusqu'à éviction LRU ou redémarrage.
2. **La clé de cache contient le dataset complet** : `_cached_prepare_survival_data(data_json_str, ...)` (survival.py:1730) et `_cached_competing_risks(data_json_str, ...)` (gvh.py:201) reçoivent le store sérialisé en JSON ; `_make_cache_key` (cache_utils.py:37) insère les arguments `str` **verbatim** dans la clé → le JSON patient complet est conservé en RAM dans les clés du dictionnaire. De plus, sérialiser le dataset à chaque appel pour construire la clé **coûte** un `json.dumps` complet par requête.
3. **Risque de fuite inter-utilisateurs** : pour les arguments `list`/`dict`, la clé utilise `id(arg)` (cache_utils.py:31) — un identifiant mémoire **réutilisé** après garbage collection ; pour les DataFrames, seuls `shape` + noms de colonnes entrent dans la clé (ligne 34) → deux jeux de données différents de même forme **collisionnent**. Un utilisateur peut donc théoriquement recevoir le résultat calculé sur les données d'un autre.

**Recommandation : supprimer ces caches.** Depuis la phase 3, les calculs sous-jacents coûtent 59 ms (Kaplan-Meier) et 83 ms (risques compétitifs) sur 16 000 lignes : le cache n'apporte quasiment rien et son retrait élimine les trois problèmes ci-dessus plus le `json.dumps` de clé à chaque appel. Le décor devient inutile ; `modules/cache_utils.py` peut être supprimé ou réduit à un module vide documenté.

## 2. `storage_type` des `dcc.Store` — conforme

Inventaire exhaustif (`grep dcc.Store`) : `data-store`, `data-store-survival`, `data-store-gvh`, `data-store-viz` (dashboard_layout.py:89-95), `metadata-store`, `pediatric-view`, `current-page`, `last-rendered-page` (app.py / dashboard_layout.py) et tous les stores de pages — **aucun ne précise `storage_type`**, donc défaut Dash = **`memory`** (volatile, jamais `local`/`session`). Conforme à la contrainte 3.

## 3. Écritures disque — aucune de données patient

Recherche `open(...'w')`, `to_csv(`, `to_excel(` sur tout le code applicatif : seuls les scripts de perf (données **synthétiques**) écrivent des fichiers. Les exports Excel/CSV « missing data » passent par `dcc.send_data_frame` (flux HTTP, pas d'écriture serveur). `access.log` à la racine du dépôt est un journal d'accès HTTP (URLs, pas de corps de requêtes ni de données patient) — à garder hors portée et à ne pas committer de version contenant des paramètres d'URL sensibles.

## 4. État global — propre hors cache_utils

Aucun attribut de données sur `app.server` (uniquement `server = app.server` pour le WSGI). Aucune variable de module mutable contenant des données patient en dehors de `cache_utils.py`. Les seuls globaux sont des constantes de config et le flag `LIFELINES_AVAILABLE`.

## 5. Logs / prints — corrigé en phase 3

- `modules/competing_risks.py` imprimait des lignes de debug **par patient** (`Patient {idx}: GvH 'Yes' mais temps...`) → supprimés dans le commit `ed37da5`.
- Restent des `print` de structure (noms de colonnes, comptages : ex. `gvh.py:208`, `data_processing.py`) — pas de données patient, mais à nettoyer ou passer en `logging` niveau DEBUG si l'on veut des logs serveur propres.
- `normalize_column_names` et autres helpers impriment des informations de schéma uniquement.

## 6. Revue nginx (hors dépôt — à vérifier côté infra)

Point critique rappelé par le plan : nginx bufferise les corps de requêtes et, au-delà de `client_body_buffer_size`, les écrit dans un **fichier temporaire sur disque** (`client_body_temp_path`) avant de les transmettre à gunicorn. Avec des requêtes `_dash-update-component` de ~57 Mo contenant des données patient (phase 1), cela **contredit l'argument « rien sur le disque du serveur »**, tant que la phase 4 n'a pas réduit le volume.

À vérifier dans la config nginx de production :

- `client_body_buffer_size` (défaut : 8k/16k) — largement dépassé par les payloads actuels → écriture disque quasi systématique ;
- `client_body_temp_path` — où tombent ces fichiers, et leur durée de vie ;
- `proxy_request_buffering off` éviterait l'écriture (streaming direct vers gunicorn) mais consomme une connexion worker pendant tout l'upload ;
- `client_max_body_size` — doit au moins accepter les payloads actuels.

**La meilleure correction reste la phase 4** : ramener les requêtes à quelques ko rend le problème sans objet (tout tient dans le buffer mémoire).

## Conclusion

Une seule non-conformité réelle côté code : **`modules/cache_utils.py` et ses 5 usages**. Sa suppression (recommandée, chiffrée, sans impact fonctionnel) rend l'audit propre. Le point nginx relève de l'infra et se résout de fait avec la phase 4.
