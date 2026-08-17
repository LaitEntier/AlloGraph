# Pages

Each page module follows the same contract: `get_layout()` returns the layout, `register_callbacks(app)` wires the interactivity. See [Adding a new page](../guides/add-page.md).

`pages/legal.py`, `pages/privacy.py`, and `pages/cookies.py` are static content pages and are omitted here.

## `pages.home`

Landing page: data upload, test sample loading, overview visualization.

::: pages.home

## `pages.patients`

Demographic distributions, age boxplots, yearly summary tables, performance scores by age group.

::: pages.patients

## `pages.hemopathies`

Main/subclass diagnosis distributions and stratifications.

::: pages.hemopathies

## `pages.procedures`

Donor type evolution, stem cell sources, CMV status, conditioning and prophylaxis analyses (including UpSet plots), aplasia durations.

::: pages.procedures

## `pages.gvh`

Acute and chronic GvHD competing risks analysis with cumulative incidence curves.

::: pages.gvh

## `pages.relapse`

Relapse vs death competing risks analysis.

::: pages.relapse

## `pages.survival`

Kaplan–Meier curves (global and by year), GRFS, long-term follow-up. Requires `lifelines`.

::: pages.survival

## `pages.toxicity`

Toxicity analysis.

::: pages.toxicity

## `pages.indics`

Clinical indicators dashboard: TRM at 30/100/365 days, overall survival, engraftment, neutrophil recovery, relapse incidence, GvHD indicators.

::: pages.indics
