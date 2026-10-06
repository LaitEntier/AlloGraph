"""
Inventaire statique des callbacks Dash (phase 1 du plan perf, lecture seule).

Parse app.py et pages/*.py via AST et produit docs/perf/callbacks.md :
- tableau de tous les callbacks (Outputs, Inputs, States, prevent_initial_call)
- signalement des callbacks recevant un store de données en Input (H1)
- heuristique « calcul lourd » (corps mentionnant iterrows / lifelines /
  CompetingRisks / upset / process_data)
- graphe de dépendances Mermaid centré sur les stores de données
"""

import ast
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / 'docs' / 'perf' / 'callbacks.md'
FILES = [REPO_ROOT / 'app.py'] + sorted((REPO_ROOT / 'pages').glob('*.py'))

# Stores contenant des données patient (volume significatif)
DATA_STORES = {'data-store', 'data-store-survival', 'data-store-gvh', 'data-store-viz'}

HEAVY_MARKERS = ['iterrows', 'CompetingRisks', 'KaplanMeier', 'kmf', 'lifelines',
                 'process_data', 'upset', 'CumulativeIncidence']


def _id_of(dep):
    """Extrait l'identifiant de composant d'un Input/Output/State."""
    if not isinstance(dep, ast.Call) or not dep.args:
        return '?'
    first = dep.args[0]
    if isinstance(first, ast.Constant):
        return str(first.value)
    if isinstance(first, ast.Dict):  # pattern-matching id
        keys = [k.value for k in first.keys if isinstance(k, ast.Constant)]
        return 'PM{' + ','.join(map(str, keys)) + '}'
    return ast.unparse(first)[:40]


def _prop_of(dep):
    if isinstance(dep, ast.Call) and len(dep.args) > 1:
        second = dep.args[1]
        if isinstance(second, ast.Constant):
            return str(second.value)
        return ast.unparse(second)[:30]
    return '?'


def _deps_of(node, names):
    """Collecte les dépendances Input/Output/State, y compris dans les listes."""
    found = []

    def visit(n):
        if isinstance(n, ast.Call):
            func = n.func
            attr = func.attr if isinstance(func, ast.Attribute) else (
                func.id if isinstance(func, ast.Name) else None)
            if attr in names:
                found.append(n)
                return  # ne pas descendre dans les args d'une dépendance
        for child in ast.iter_child_nodes(n):
            visit(child)

    visit(node)
    return found


def analyze_file(path):
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source)
    results = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            attr = func.attr if isinstance(func, ast.Attribute) else (
                func.id if isinstance(func, ast.Name) else None)
            if attr not in ('callback', 'clientside_callback'):
                continue

            outputs, inputs, states = [], [], []
            for arg in dec.args:
                outputs.extend(_deps_of(arg, {'Output'}))
                inputs.extend(_deps_of(arg, {'Input'}))
                states.extend(_deps_of(arg, {'State'}))
            for kw in dec.keywords:
                outputs.extend(_deps_of(kw.value, {'Output'}))
                inputs.extend(_deps_of(kw.value, {'Input'}))
                states.extend(_deps_of(kw.value, {'State'}))

            pic = None
            for kw in dec.keywords:
                if kw.arg == 'prevent_initial_call' and isinstance(kw.value, ast.Constant):
                    pic = kw.value.value

            body = '\n'.join(lines[node.lineno - 1:node.end_lineno])
            heavy = [m for m in HEAVY_MARKERS if m in body]

            results.append({
                'file': path.name if path.parent.name == 'pages' else 'app.py',
                'line': node.lineno,
                'function': node.name,
                'clientside': attr == 'clientside_callback',
                'outputs': [f'{_id_of(o)}.{_prop_of(o)}' for o in outputs],
                'inputs': [f'{_id_of(i)}.{_prop_of(i)}' for i in inputs],
                'states': [f'{_id_of(s)}.{_prop_of(s)}' for s in states],
                'prevent_initial_call': pic,
                'heavy': heavy,
            })
            break  # un seul décorateur callback par fonction
    return results


def main():
    all_cbs = []
    for f in FILES:
        if f.name == '__init__.py':
            continue
        all_cbs.extend(analyze_file(f))

    def store_in(deps):
        return sorted({d.split('.')[0] for d in deps if d.split('.')[0] in DATA_STORES})

    md = []
    md.append('# Phase 1 — Inventaire des callbacks')
    md.append('')
    md.append(f"Date : {date.today().isoformat()}. Généré par `scripts/perf/callback_inventory.py` (analyse AST, lecture seule).")
    md.append('')

    # --- Statistiques globales ---
    n = len(all_cbs)
    with_store_input = [c for c in all_cbs if store_in(c['inputs'])]
    with_store_state = [c for c in all_cbs if store_in(c['states']) and not store_in(c['inputs'])]
    full_store_input = [c for c in all_cbs if 'data-store' in store_in(c['inputs'])]
    heavy = [c for c in all_cbs if c['heavy']]
    no_pic_store = [c for c in with_store_input if c['prevent_initial_call'] is not True]

    md.append('## Statistiques globales')
    md.append('')
    md.append(f"- **{n} callbacks** serveur au total")
    md.append(f"- **{len(with_store_input)} reçoivent un store de données en `Input`** "
              f"(→ le dataset traverse le réseau et est redécodé à chaque déclenchement — H1)")
    md.append(f"  - dont **{len(full_store_input)} reçoivent `data-store` (dataset complet)**")
    md.append(f"- {len(with_store_state)} reçoivent un store de données en `State` uniquement")
    md.append(f"- **{len(no_pic_store)} callbacks avec store en `Input` sans `prevent_initial_call=True`** "
              f"(se déclenchent au chargement de page)")
    md.append(f"- {len(heavy)} callbacks à calcul potentiellement lourd (heuristique : "
              + ', '.join(f'`{m}`' for m in HEAVY_MARKERS) + ')')
    md.append('')
    per_file = defaultdict(int)
    for c in all_cbs:
        per_file[c['file']] += 1
    md.append('Répartition : ' + ', '.join(f"`{f}` {k}" for f, k in sorted(per_file.items())))
    md.append('')

    # --- Callbacks critiques (H1) ---
    md.append('## Callbacks recevant un store de données en `Input` (H1)')
    md.append('')
    md.append('| Fichier | Fonction | Stores en Input | Stores en State | Calcul lourd ? | PIC |')
    md.append('|---|---|---|---|---|---|')
    for c in with_store_input:
        md.append(
            f"| {c['file']}:{c['line']} | `{c['function']}` | {', '.join(store_in(c['inputs']))} | "
            f"{', '.join(store_in(c['states'])) or '—'} | {', '.join(c['heavy']) or '—'} | "
            f"{c['prevent_initial_call']} |")
    md.append('')

    # --- Tableau complet ---
    md.append('## Tableau complet des callbacks')
    md.append('')
    md.append('| Fichier | Fonction | Outputs | Inputs | States | PIC | Lourd ? |')
    md.append('|---|---|---|---|---|---|---|')
    for c in all_cbs:
        def fmt(deps):
            return '<br>'.join(f'`{d}`' for d in deps) or '—'
        md.append(
            f"| {c['file']}:{c['line']} | `{c['function']}` | {fmt(c['outputs'])} | "
            f"{fmt(c['inputs'])} | {fmt(c['states'])} | {c['prevent_initial_call']} | "
            f"{', '.join(c['heavy']) or '—'} |")
    md.append('')

    # --- Graphe Mermaid : flux des stores de données ---
    md.append('## Graphe de dépendances (stores de données)')
    md.append('')
    md.append('Flux : store → callback → outputs. Nœuds de données en majuscules.')
    md.append('')
    md.append('```mermaid')
    md.append('flowchart LR')
    for s in sorted(DATA_STORES):
        md.append(f'    {s.replace("-", "_")}["{s}"]')
    md.append('')
    for c in all_cbs:
        cb_id = f"cb_{c['file'].replace('.py', '')}_{c['function']}".replace('-', '_')
        ins = store_in(c['inputs']) + store_in(c['states'])
        if not ins:
            continue
        style = 'heavy' if c['heavy'] else 'light'
        md.append(f'    {cb_id}["{c["function"]}<br><i>{c["file"]}</i>"]:::{style}')
        for s in ins:
            arrow = '-->' if s in store_in(c['inputs']) else '-.State.->'
            md.append(f'    {s.replace("-", "_")} {arrow} {cb_id}')
        for o in c['outputs']:
            out_id = 'out_' + o.split('.')[0].replace('-', '_').replace('{', '').replace('}', '').replace(',', '_')
            md.append(f'    {cb_id} --> {out_id}["{o}"]')
    md.append('')
    md.append('    classDef heavy fill:#f8d7da,stroke:#c0392b;')
    md.append('    classDef light fill:#d4edda,stroke:#2e7d32;')
    md.append('```')
    md.append('')

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text('\n'.join(md), encoding='utf-8')
    print(f"{n} callbacks inventoriés -> {REPORT_PATH}")
    print(f"Dont {len(with_store_input)} avec store de données en Input "
          f"({len(full_store_input)} avec data-store complet)")


if __name__ == '__main__':
    main()
