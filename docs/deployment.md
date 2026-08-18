# Deployment & performance

## Heroku

The repository includes a `Procfile`:

```
web: gunicorn app:server
```

`app.py` exposes the Flask `server` object that gunicorn serves. Alternatively, `wsgi.py` is a standard WSGI entry point:

```bash
python wsgi.py
```

## Performance on VM deployments

Network latency between client and server dominates on VM setups. The app mitigates it in four ways:

### 1. Slim data stores

The dataset is split into specialized `dcc.Store`s (`data-store-survival`, `data-store-gvh`, `data-store-viz`) so callbacks only transfer the columns they need. Keep them in mind when adding derived columns — see [Architecture](getting-started/architecture.md#slim-data-stores).

### 2. In-memory caching

Expensive statistics (lifelines fits, competing risks) are cached via `modules/cache_utils.py`:

- in-memory only, cleared on restart — no disk persistence (GDPR-friendly)
- cache keys are content hashes — no PHI in keys
- session-scoped

### 3. Response compression

If `flask-compress` is installed, JSON responses are gzip-compressed:

```bash
pip install flask-compress
```

The app runs fine without it (a note is printed at startup).

### 4. Callback hygiene

Heavy callbacks use `prevent_initial_call=True` so they don't fire on page load or on store initialization. Follow this convention for any new expensive callback.

## Security & GDPR

The application processes potentially sensitive medical data. Current posture:

- Uploaded data lives **client-side only** (Dash stores in the browser)
- No server-side persistence; uploads are processed in memory and never written to disk
- Caching is in-memory, non-persistent, PHI-free

For a production deployment with real patient data, add at minimum:

- HTTPS enforcement
- Authentication / authorization
- Audit logging
- Encryption at rest if you introduce any server-side storage

## Logging

`access.log` / `server.log` may exist locally — they are runtime artifacts, not part of the codebase.
