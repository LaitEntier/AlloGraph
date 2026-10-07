# Phase 5 — Revue de la configuration gunicorn (propositions, rien d'appliqué)

Date : 2026-10-06.

## Config actuelle

- `Procfile` : `web: gunicorn app:server` — **aucun réglage dans le dépôt** (workers, timeout, threads : valeurs par défaut ou configurées hors dépôt).
- Production (d'après le brief) : 4 workers derrière nginx, VM 4 vCPU / 7,8 Go.
- Défauts gunicorn concernés : `--timeout 30`, worker class `sync`, pas de `--max-requests`.

## Analyse

- **Workers = 4 sur 4 vCPU : correct** pour du calcul CPU-bound en workers sync (un traitement Python = un cœur, GIL). Ne pas augmenter au-delà des cœurs.
- **Threads : inutiles pour le calcul** (GIL) — ils n'accélèrent que l'attente d'E/S. Inutile ici ; ne pas activer en espérant du gain CPU.
- **Timeout 30 s : non bloquant après la phase 3.** Les calculs les plus lents mesurés : `process_data` 213 ms, risques compétitifs 83 ms, Kaplan-Meier 59 ms (16 000 lignes). Même avec la désérialisation JSON du payload (~0,3 s), une requête reste < 2 s. Avant la phase 3, le même traitement pouvait approcher plusieurs secondes — le timeout ne tuait probablement pas de workers, mais il n'y avait pas de marge. C'est bon désormais.
- **Payloads géants** : les requêtes `_dash-update-component` de ~57 Mo (phase 1) allongent le temps de réception de chaque requête et occupent un worker pendant la lecture du corps. C'est un argument supplémentaire pour la phase 4 (réduction du volume), pas pour un changement gunicorn.

## Propositions (non appliquées)

1. **Ajouter `--max-requests 1000 --max-requests-jitter 100`** : recycle périodiquement les workers. Borne la croissance mémoire et garantit la purge des caches en RAM (tant que `modules/cache_utils.py` existe — voir phase 6). C'est cohérent avec l'objectif « rien de persistant côté serveur ».
2. **Explicitier les réglages dans le dépôt** (ex. `gunicorn.conf.py` versionné, sans toucher à la prod) : `workers = 4`, `timeout = 30`, `max_requests`, pour rendre la config reproductible et reviewable.
3. **Ne pas** ajouter de threads ni de workers supplémentaires.
4. Côté nginx (hors dépôt, voir phase 6 §3) : vérifier que `client_max_body_size` accepte les payloads actuels tant que la phase 4 n'a pas réduit le volume.

## Verdict

La config gunicorn n'est **pas** un goulot. Les gains sont dans l'application (phases 3 et 4). Les seules propositions utiles : `--max-requests` (hygiène mémoire/conformité) et une config versionnée.
