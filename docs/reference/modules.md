# Core modules

## `modules.data_processing`

Data loading, column normalization, cleaning, and all derived variables. Main entry points: `load_data()` and `process_data()`.

::: modules.data_processing

## `modules.dashboard_layout`

Shared UI components: sidebar builders, navigation, and reusable filter helpers (`apply_age_filter`, `apply_malignancy_filter`, …).

::: modules.dashboard_layout

## `modules.competing_risks`

Competing risks statistical analysis (cumulative incidence), used by the GvH and Relapse pages.

::: modules.competing_risks

## `modules.cache_utils`

In-memory caching decorator for expensive computations (see [Deployment & performance](../deployment.md#2-in-memory-caching)).

::: modules.cache_utils

## `modules.validation`

Placeholder for data validation.

::: modules.validation

## `modules.callbacks`

Placeholder for shared callbacks.

::: modules.callbacks
