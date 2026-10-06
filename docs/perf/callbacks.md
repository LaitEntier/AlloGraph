# Phase 1 — Inventaire des callbacks

Date : 2026-10-06. Généré par `scripts/perf/callback_inventory.py` (analyse AST, lecture seule).

## Statistiques globales

- **73 callbacks** serveur au total
- **46 reçoivent un store de données en `Input`** (→ le dataset traverse le réseau et est redécodé à chaque déclenchement — H1)
  - dont **38 reçoivent `data-store` (dataset complet)**
- 0 reçoivent un store de données en `State` uniquement
- **46 callbacks avec store en `Input` sans `prevent_initial_call=True`** (se déclenchent au chargement de page)
- 15 callbacks à calcul potentiellement lourd (heuristique : `iterrows`, `CompetingRisks`, `KaplanMeier`, `kmf`, `lifelines`, `process_data`, `upset`, `CumulativeIncidence`)

Répartition : `app.py` 11, `gvh.py` 5, `hemopathies.py` 7, `home.py` 4, `indics.py` 9, `patients.py` 9, `procedures.py` 9, `relapse.py` 4, `survival.py` 11, `toxicity.py` 4

## Callbacks recevant un store de données en `Input` (H1)

| Fichier | Fonction | Stores en Input | Stores en State | Calcul lourd ? | PIC |
|---|---|---|---|---|---|
| app.py:150 | `navigate` | data-store | — | — | None |
| app.py:243 | `update_sidebar` | data-store | — | — | None |
| app.py:444 | `toggle_sidebar_visibility` | data-store | — | — | None |
| app.py:584 | `update_slim_stores` | data-store | — | — | None |
| app.py:717 | `toggle_purge_button_visibility` | data-store | — | — | None |
| gvh.py:261 | `update_grade_filters` | data-store | — | — | False |
| gvh.py:358 | `update_gvh_main_graph` | data-store-gvh | — | — | None |
| gvh.py:406 | `gvh_missing_summary_callback` | data-store | — | — | False |
| gvh.py:525 | `gvh_missing_detail_callback` | data-store | — | iterrows | False |
| hemopathies.py:187 | `update_simple_barplot` | data-store | — | — | None |
| hemopathies.py:308 | `update_normalized_barplot` | data-store | — | — | None |
| hemopathies.py:416 | `update_performance_scores_boxplot` | data-store | — | — | None |
| hemopathies.py:611 | `update_hemopathies_datatable` | data-store | — | — | None |
| hemopathies.py:800 | `hemopathies_missing_summary_callback` | data-store | — | — | False |
| hemopathies.py:891 | `hemopathies_missing_detail_callback` | data-store | — | iterrows | False |
| home.py:545 | `update_home_content` | data-store | — | — | None |
| indics.py:3916 | `update_indicator_content` | data-store | — | — | False |
| indics.py:3981 | `indicators_missing_summary_callback` | data-store | — | — | False |
| indics.py:4077 | `indicators_missing_detail_callback` | data-store | — | iterrows | False |
| patients.py:225 | `update_normalized_chart` | data-store-viz | — | — | None |
| patients.py:326 | `update_distribution_chart` | data-store-viz | — | — | None |
| patients.py:427 | `update_boxplot_chart` | data-store-viz | — | — | None |
| patients.py:509 | `update_datatable` | data-store | — | — | None |
| patients.py:773 | `update_patients_performance_scores_boxplot` | data-store-viz | — | — | None |
| patients.py:971 | `patients_missing_summary_callback` | data-store | — | — | False |
| patients.py:1062 | `patients_missing_detail_callback` | data-store | — | iterrows | False |
| procedures.py:277 | `update_main_variable_options` | data-store | — | — | False |
| procedures.py:314 | `update_main_chart` | data-store | — | — | None |
| procedures.py:396 | `update_cmv_charts` | data-store | — | — | None |
| procedures.py:445 | `update_aplasia_tab_content` | data-store | — | — | None |
| procedures.py:648 | `update_treatment_chart` | data-store | — | upset | None |
| procedures.py:755 | `update_prophylaxis_chart` | data-store | — | upset | None |
| procedures.py:854 | `procedures_missing_summary_callback` | data-store | — | — | False |
| procedures.py:970 | `procedures_missing_detail_callback` | data-store | — | iterrows | False |
| relapse.py:364 | `update_relapse_main_graph` | data-store | — | — | None |
| relapse.py:403 | `relapse_missing_summary_callback` | data-store | — | — | False |
| relapse.py:516 | `relapse_missing_detail_callback` | data-store | — | iterrows | False |
| survival.py:1650 | `update_gvh_filters_container` | data-store | — | — | None |
| survival.py:1771 | `update_global_survival_curve` | data-store-survival | — | lifelines | None |
| survival.py:1855 | `update_survival_curves_by_year` | data-store-survival | — | lifelines | None |
| survival.py:2017 | `update_survival_grfs_graph` | data-store-survival | — | lifelines | None |
| survival.py:2165 | `survival_missing_summary_callback` | data-store | — | — | False |
| survival.py:2271 | `survival_missing_detail_callback` | data-store | — | iterrows | False |
| toxicity.py:384 | `update_toxicity_nrm_graph` | data-store | — | — | None |
| toxicity.py:421 | `toxicity_missing_summary_callback` | data-store | — | — | False |
| toxicity.py:535 | `toxicity_missing_detail_callback` | data-store | — | iterrows | False |

## Tableau complet des callbacks

| Fichier | Fonction | Outputs | Inputs | States | PIC | Lourd ? |
|---|---|---|---|---|---|---|
| app.py:150 | `navigate` | `current-page.data`<br>`nav-home.className`<br>`nav-patients.className`<br>`nav-hemopathies.className`<br>`nav-procedures.className`<br>`nav-gvh.className`<br>`nav-relapse.className`<br>`nav-survival.className`<br>`nav-toxicity.className`<br>`nav-indics.className`<br>`nav-patients.disabled`<br>`nav-hemopathies.disabled`<br>`nav-procedures.disabled`<br>`nav-gvh.disabled`<br>`nav-relapse.disabled`<br>`nav-survival.disabled`<br>`nav-toxicity.disabled`<br>`nav-indics.disabled` | `nav-home.n_clicks`<br>`nav-home-logo.n_clicks`<br>`nav-patients.n_clicks`<br>`nav-hemopathies.n_clicks`<br>`nav-procedures.n_clicks`<br>`nav-gvh.n_clicks`<br>`nav-relapse.n_clicks`<br>`nav-survival.n_clicks`<br>`nav-toxicity.n_clicks`<br>`nav-indics.n_clicks`<br>`footer-nav-legal.n_clicks`<br>`footer-nav-privacy.n_clicks`<br>`footer-nav-cookies.n_clicks`<br>`data-store.data` | `current-page.data` | None | — |
| app.py:243 | `update_sidebar` | `sidebar-content.children` | `current-page.data`<br>`data-store.data`<br>`metadata-store.data`<br>`pediatric-view.data` | — | None | — |
| app.py:433 | `update_pediatric_view` | `pediatric-view.data` | `pediatric-view-switch.value` | — | True | — |
| app.py:444 | `toggle_sidebar_visibility` | `sidebar-content.style`<br>`main-content.width` | `current-page.data`<br>`data-store.data` | — | None | — |
| app.py:467 | `process_uploaded_file` | `data-store.data`<br>`metadata-store.data`<br>`upload-status.children` | `upload-data.contents` | `upload-data.filename` | True | process_data |
| app.py:584 | `update_slim_stores` | `data-store-survival.data`<br>`data-store-gvh.data`<br>`data-store-viz.data` | `data-store.data` | — | None | — |
| app.py:614 | `update_main_content` | `main-content.children`<br>`last-rendered-page.data` | `current-page.data` | `last-rendered-page.data` | None | — |
| app.py:679 | `toggle_purge_modal` | `purge-confirmation-modal.is_open` | `purge-data-button.n_clicks`<br>`cancel-purge.n_clicks`<br>`confirm-purge.n_clicks` | `purge-confirmation-modal.is_open` | None | — |
| app.py:705 | `purge_data` | `data-store.data`<br>`metadata-store.data`<br>`data-store-survival.data`<br>`data-store-gvh.data`<br>`data-store-viz.data` | `confirm-purge.n_clicks` | — | True | — |
| app.py:717 | `toggle_purge_button_visibility` | `purge-data-button.style` | `data-store.data` | — | None | — |
| app.py:731 | `load_test_sample` | `data-store.data`<br>`metadata-store.data`<br>`upload-status.children` | `load-test-sample-btn.n_clicks` | — | True | process_data |
| gvh.py:261 | `update_grade_filters` | `gvh-grade-filter-container.children` | `gvh-type-selection.value`<br>`data-store.data` | — | False | — |
| gvh.py:358 | `update_gvh_main_graph` | `gvh-main-graph.children` | `gvh-type-selection.value`<br>`gvh-year-filter.value`<br>`gvh-grade-filter.value`<br>`gvh-age-filter.value`<br>`gvh-custom-age-switch.value`<br>`gvh-custom-age-slider.value`<br>`gvh-malignancy-filter.value`<br>`data-store-gvh.data`<br>`current-page.data` | — | None | — |
| gvh.py:406 | `gvh_missing_summary_callback` | `gvh-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`gvh-year-filter.value`<br>`gvh-age-filter.value`<br>`gvh-custom-age-switch.value`<br>`gvh-custom-age-slider.value`<br>`gvh-malignancy-filter.value` | — | False | — |
| gvh.py:525 | `gvh_missing_detail_callback` | `gvh-missing-detail-table.children`<br>`export-missing-gvh-button.disabled`<br>`gvh-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`gvh-year-filter.value`<br>`gvh-age-filter.value`<br>`gvh-custom-age-switch.value`<br>`gvh-custom-age-slider.value`<br>`gvh-malignancy-filter.value` | — | False | iterrows |
| gvh.py:611 | `export_missing_gvh_excel` | `download-missing-gvh-excel.data` | `export-missing-gvh-button.n_clicks` | `gvh-missing-store.data` | True | — |
| hemopathies.py:187 | `update_simple_barplot` | `hemopathies-barplot-simple.children` | `data-store.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`stack-variable-dropdown.value`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | None | — |
| hemopathies.py:308 | `update_normalized_barplot` | `hemopathies-barplot-normalized.children` | `data-store.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`stack-variable-dropdown.value`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | None | — |
| hemopathies.py:416 | `update_performance_scores_boxplot` | `hemopathies-performance-scores-boxplot.children` | `data-store.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | None | — |
| hemopathies.py:611 | `update_hemopathies_datatable` | `hemopathies-datatable.children` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | None | — |
| hemopathies.py:800 | `hemopathies_missing_summary_callback` | `hemopathies-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | False | — |
| hemopathies.py:891 | `hemopathies_missing_detail_callback` | `hemopathies-missing-detail-table.children`<br>`export-missing-hemopathies-button.disabled`<br>`hemopathies-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`hemopathies-age-filter.value`<br>`hemopathies-malignancy-filter.value`<br>`hemopathies-custom-age-switch.value`<br>`hemopathies-custom-age-slider.value` | — | False | iterrows |
| hemopathies.py:971 | `export_missing_hemopathies_excel` | `download-missing-hemopathies-excel.data` | `export-missing-hemopathies-button.n_clicks` | `hemopathies-missing-store.data` | True | — |
| home.py:545 | `update_home_content` | `home-main-content.children` | `data-store.data` | — | None | — |
| home.py:619 | `toggle_template_collapse` | `template-collapse.is_open`<br>`template-chevron.className` | `template-collapse-btn.n_clicks` | `template-collapse.is_open` | True | — |
| home.py:633 | `download_template` | `download-template.data` | `download-template-btn.n_clicks` | — | True | — |
| home.py:646 | `toggle_tutorial_collapse` | `tutorial-collapse.is_open`<br>`tutorial-chevron.className` | `tutorial-collapse-btn.n_clicks` | `tutorial-collapse.is_open` | True | — |
| indics.py:3866 | `update_indicator_store` | `selected-indicator-store.data` | `indicator-selection-sidebar.value` | — | True | — |
| indics.py:3875 | `update_year_store` | `selected-year-store.data` | `year-selection-sidebar.value` | — | True | — |
| indics.py:3884 | `update_years_radio_store` | `selected-years-checklist-store.data` | `years-radio-sidebar.value` | — | False | — |
| indics.py:3895 | `toggle_analysis_mode` | `analysis-mode-store.data`<br>`yearly-controls.style`<br>`quarterly-controls.style` | `analysis-mode-radio.value` | — | False | — |
| indics.py:3916 | `update_indicator_content` | `indicator-content.children` | `current-page.data`<br>`data-store.data`<br>`analysis-mode-store.data`<br>`selected-indicator-store.data`<br>`selected-year-store.data`<br>`selected-years-checklist-store.data`<br>`indicators-age-filter.value`<br>`indicators-custom-age-switch.value`<br>`indicators-custom-age-slider.value`<br>`indicators-malignancy-filter.value` | — | False | — |
| indics.py:3959 | `update_missing_subtitle` | `indicators-missing-subtitle.children` | `selected-indicator-store.data`<br>`current-page.data` | — | False | — |
| indics.py:3981 | `indicators_missing_summary_callback` | `indicators-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`selected-indicator-store.data`<br>`analysis-mode-store.data`<br>`year-selection-sidebar.value`<br>`years-radio-sidebar.value`<br>`indicators-age-filter.value`<br>`indicators-custom-age-switch.value`<br>`indicators-custom-age-slider.value`<br>`indicators-malignancy-filter.value` | — | False | — |
| indics.py:4077 | `indicators_missing_detail_callback` | `indicators-missing-detail-table.children`<br>`export-missing-indicators-button.disabled`<br>`indicators-missing-store.data`<br>`indicators-name-store.data` | `data-store.data`<br>`current-page.data`<br>`selected-indicator-store.data`<br>`analysis-mode-store.data`<br>`year-selection-sidebar.value`<br>`years-radio-sidebar.value`<br>`indicators-age-filter.value`<br>`indicators-custom-age-switch.value`<br>`indicators-custom-age-slider.value`<br>`indicators-malignancy-filter.value` | — | False | iterrows |
| indics.py:4161 | `export_missing_indicators_excel` | `download-missing-indicators-excel.data` | `export-missing-indicators-button.n_clicks` | `indicators-missing-store.data`<br>`indicators-name-store.data` | True | — |
| patients.py:225 | `update_normalized_chart` | `patients-normalized-chart.children` | `data-store-viz.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`stack-variable-dropdown.value`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`pediatric-view.data`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | None | — |
| patients.py:326 | `update_distribution_chart` | `patients-distribution-chart.children` | `data-store-viz.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`stack-variable-dropdown.value`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`pediatric-view.data`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | None | — |
| patients.py:427 | `update_boxplot_chart` | `patients-boxplot-chart.children` | `data-store-viz.data`<br>`current-page.data`<br>`x-axis-dropdown.value`<br>`stack-variable-dropdown.value`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | None | — |
| patients.py:509 | `update_datatable` | `patients-datatable.children`<br>`export-csv-button.disabled`<br>`patients-stats-store.data` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | None | — |
| patients.py:729 | `export_csv` | `download-csv.data` | `export-csv-button.n_clicks` | `year-filter-checklist.value`<br>`patients-stats-store.data` | True | — |
| patients.py:773 | `update_patients_performance_scores_boxplot` | `patients-performance-scores-boxplot.children` | `data-store-viz.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`pediatric-view.data`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | None | — |
| patients.py:971 | `patients_missing_summary_callback` | `patients-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | False | — |
| patients.py:1062 | `patients_missing_detail_callback` | `patients-missing-detail-table.children`<br>`export-missing-patients-button.disabled`<br>`patients-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`year-filter-checklist.value`<br>`patients-age-filter.value`<br>`patients-malignancy-filter.value`<br>`patients-custom-age-switch.value`<br>`patients-custom-age-slider.value` | — | False | iterrows |
| patients.py:1144 | `export_missing_patients_excel` | `download-missing-patients-excel.data` | `export-missing-patients-button.n_clicks` | `patients-missing-store.data` | True | — |
| procedures.py:277 | `update_main_variable_options` | `procedures-main-variable-integrated.options`<br>`procedures-main-variable-integrated.value` | `data-store.data`<br>`current-page.data` | — | False | — |
| procedures.py:314 | `update_main_chart` | `procedures-main-chart.children` | `data-store.data`<br>`current-page.data`<br>`procedures-main-variable-integrated.value`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | None | — |
| procedures.py:396 | `update_cmv_charts` | `procedures-cmv-charts.children` | `data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | None | — |
| procedures.py:445 | `update_aplasia_tab_content` | `procedures-aplasia-tab-content.children` | `procedures-aplasia-tabs.value`<br>`data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | None | — |
| procedures.py:648 | `update_treatment_chart` | `procedures-treatment-content.children` | `procedures-treatment-tabs.value`<br>`data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | None | upset |
| procedures.py:755 | `update_prophylaxis_chart` | `procedures-prophylaxis-content.children` | `procedures-prophylaxis-tabs.value`<br>`data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | None | upset |
| procedures.py:854 | `procedures_missing_summary_callback` | `procedures-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | False | — |
| procedures.py:970 | `procedures_missing_detail_callback` | `procedures-missing-detail-table.children`<br>`export-missing-procedures-button.disabled`<br>`procedures-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`procedures-year-filter.value`<br>`procedures-age-filter.value`<br>`procedures-custom-age-switch.value`<br>`procedures-custom-age-slider.value`<br>`procedures-malignancy-filter.value` | — | False | iterrows |
| procedures.py:1051 | `export_missing_procedures_excel` | `download-missing-procedures-excel.data` | `export-missing-procedures-button.n_clicks` | `procedures-missing-store.data` | True | — |
| relapse.py:364 | `update_relapse_main_graph` | `relapse-main-graph.children` | `relapse-year-filter.value`<br>`relapse-age-filter.value`<br>`relapse-custom-age-switch.value`<br>`relapse-custom-age-slider.value`<br>`relapse-malignancy-filter.value`<br>`data-store.data`<br>`current-page.data` | — | None | — |
| relapse.py:403 | `relapse_missing_summary_callback` | `relapse-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`relapse-year-filter.value`<br>`relapse-age-filter.value`<br>`relapse-custom-age-switch.value`<br>`relapse-custom-age-slider.value`<br>`relapse-malignancy-filter.value` | — | False | — |
| relapse.py:516 | `relapse_missing_detail_callback` | `relapse-missing-detail-table.children`<br>`export-missing-relapse-button.disabled`<br>`relapse-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`relapse-year-filter.value`<br>`relapse-age-filter.value`<br>`relapse-custom-age-switch.value`<br>`relapse-custom-age-slider.value`<br>`relapse-malignancy-filter.value` | — | False | iterrows |
| relapse.py:597 | `export_missing_relapse_excel` | `download-missing-relapse-excel.data` | `export-missing-relapse-button.n_clicks` | `relapse-missing-store.data` | True | — |
| survival.py:1568 | `sync_from_tab_0` | `survival-tab-store.data` | `survival-tabs-0.value` | `survival-tab-store.data` | True | — |
| survival.py:1581 | `sync_from_tab_1` | `survival-tab-store.data` | `survival-tabs-1.value` | `survival-tab-store.data` | True | — |
| survival.py:1594 | `sync_from_tab_2` | `survival-tab-store.data` | `survival-tabs-2.value` | `survival-tab-store.data` | True | — |
| survival.py:1610 | `update_survival_headers` | `survival-header-0.children`<br>`survival-header-1.children`<br>`survival-header-2.children` | `survival-tab-store.data` | — | None | — |
| survival.py:1650 | `update_gvh_filters_container` | `survival-gvh-filters-container.children` | `survival-tab-store.data`<br>`data-store.data` | — | None | — |
| survival.py:1771 | `update_global_survival_curve` | `survival-global-curve.children` | `data-store-survival.data`<br>`current-page.data`<br>`survival-max-duration.value`<br>`survival-year-filter.value`<br>`survival-age-filter.value`<br>`survival-custom-age-switch.value`<br>`survival-custom-age-slider.value`<br>`survival-malignancy-filter.value` | — | None | lifelines |
| survival.py:1855 | `update_survival_curves_by_year` | `survival-curves-by-year.children`<br>`survival-stats-table.children` | `data-store-survival.data`<br>`current-page.data`<br>`survival-max-duration.value`<br>`survival-year-filter.value`<br>`survival-age-filter.value`<br>`survival-custom-age-switch.value`<br>`survival-custom-age-slider.value`<br>`survival-malignancy-filter.value` | — | None | lifelines |
| survival.py:2017 | `update_survival_grfs_graph` | `survival-grfs-graph.children`<br>`survival-grfs-curves-by-year.children`<br>`survival-grfs-stats-table.children` | `data-store-survival.data`<br>`current-page.data`<br>`survival-max-duration.value`<br>`survival-year-filter.value`<br>`survival-age-filter.value`<br>`survival-custom-age-switch.value`<br>`survival-custom-age-slider.value`<br>`survival-malignancy-filter.value`<br>`survival-agvh-grade-filter.value`<br>`survival-cgvh-grade-filter.value` | — | None | lifelines |
| survival.py:2165 | `survival_missing_summary_callback` | `survival-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`survival-year-filter.value`<br>`survival-age-filter.value`<br>`survival-custom-age-switch.value`<br>`survival-custom-age-slider.value`<br>`survival-malignancy-filter.value`<br>`survival-tabs-0.value` | — | False | — |
| survival.py:2271 | `survival_missing_detail_callback` | `survival-missing-detail-table.children`<br>`export-missing-survival-button.disabled`<br>`survival-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`survival-year-filter.value`<br>`survival-age-filter.value`<br>`survival-custom-age-switch.value`<br>`survival-custom-age-slider.value`<br>`survival-malignancy-filter.value`<br>`survival-tabs-0.value` | — | False | iterrows |
| survival.py:2365 | `export_missing_survival_excel` | `download-missing-survival-excel.data` | `export-missing-survival-button.n_clicks` | `survival-missing-store.data` | True | — |
| toxicity.py:384 | `update_toxicity_nrm_graph` | `toxicity-nrm-graph.children` | `toxicity-year-filter.value`<br>`toxicity-age-filter.value`<br>`toxicity-custom-age-switch.value`<br>`toxicity-custom-age-slider.value`<br>`toxicity-malignancy-filter.value`<br>`data-store.data`<br>`current-page.data` | — | None | — |
| toxicity.py:421 | `toxicity_missing_summary_callback` | `toxicity-missing-summary-table.children` | `data-store.data`<br>`current-page.data`<br>`toxicity-year-filter.value`<br>`toxicity-age-filter.value`<br>`toxicity-custom-age-switch.value`<br>`toxicity-custom-age-slider.value`<br>`toxicity-malignancy-filter.value` | — | False | — |
| toxicity.py:535 | `toxicity_missing_detail_callback` | `toxicity-missing-detail-table.children`<br>`export-missing-toxicity-button.disabled`<br>`toxicity-missing-store.data` | `data-store.data`<br>`current-page.data`<br>`toxicity-year-filter.value`<br>`toxicity-age-filter.value`<br>`toxicity-custom-age-switch.value`<br>`toxicity-custom-age-slider.value`<br>`toxicity-malignancy-filter.value` | — | False | iterrows |
| toxicity.py:612 | `export_missing_toxicity_excel` | `download-missing-toxicity-excel.data` | `export-missing-toxicity-button.n_clicks` | `toxicity-missing-store.data` | True | — |

## Graphe de dépendances (stores de données)

Flux : store → callback → outputs. Nœuds de données en majuscules.

```mermaid
flowchart LR
    data_store["data-store"]
    data_store_gvh["data-store-gvh"]
    data_store_survival["data-store-survival"]
    data_store_viz["data-store-viz"]

    cb_app_navigate["navigate<br><i>app.py</i>"]:::light
    data_store --> cb_app_navigate
    cb_app_navigate --> out_current_page["current-page.data"]
    cb_app_navigate --> out_nav_home["nav-home.className"]
    cb_app_navigate --> out_nav_patients["nav-patients.className"]
    cb_app_navigate --> out_nav_hemopathies["nav-hemopathies.className"]
    cb_app_navigate --> out_nav_procedures["nav-procedures.className"]
    cb_app_navigate --> out_nav_gvh["nav-gvh.className"]
    cb_app_navigate --> out_nav_relapse["nav-relapse.className"]
    cb_app_navigate --> out_nav_survival["nav-survival.className"]
    cb_app_navigate --> out_nav_toxicity["nav-toxicity.className"]
    cb_app_navigate --> out_nav_indics["nav-indics.className"]
    cb_app_navigate --> out_nav_patients["nav-patients.disabled"]
    cb_app_navigate --> out_nav_hemopathies["nav-hemopathies.disabled"]
    cb_app_navigate --> out_nav_procedures["nav-procedures.disabled"]
    cb_app_navigate --> out_nav_gvh["nav-gvh.disabled"]
    cb_app_navigate --> out_nav_relapse["nav-relapse.disabled"]
    cb_app_navigate --> out_nav_survival["nav-survival.disabled"]
    cb_app_navigate --> out_nav_toxicity["nav-toxicity.disabled"]
    cb_app_navigate --> out_nav_indics["nav-indics.disabled"]
    cb_app_update_sidebar["update_sidebar<br><i>app.py</i>"]:::light
    data_store --> cb_app_update_sidebar
    cb_app_update_sidebar --> out_sidebar_content["sidebar-content.children"]
    cb_app_toggle_sidebar_visibility["toggle_sidebar_visibility<br><i>app.py</i>"]:::light
    data_store --> cb_app_toggle_sidebar_visibility
    cb_app_toggle_sidebar_visibility --> out_sidebar_content["sidebar-content.style"]
    cb_app_toggle_sidebar_visibility --> out_main_content["main-content.width"]
    cb_app_update_slim_stores["update_slim_stores<br><i>app.py</i>"]:::light
    data_store --> cb_app_update_slim_stores
    cb_app_update_slim_stores --> out_data_store_survival["data-store-survival.data"]
    cb_app_update_slim_stores --> out_data_store_gvh["data-store-gvh.data"]
    cb_app_update_slim_stores --> out_data_store_viz["data-store-viz.data"]
    cb_app_toggle_purge_button_visibility["toggle_purge_button_visibility<br><i>app.py</i>"]:::light
    data_store --> cb_app_toggle_purge_button_visibility
    cb_app_toggle_purge_button_visibility --> out_purge_data_button["purge-data-button.style"]
    cb_gvh_update_grade_filters["update_grade_filters<br><i>gvh.py</i>"]:::light
    data_store --> cb_gvh_update_grade_filters
    cb_gvh_update_grade_filters --> out_gvh_grade_filter_container["gvh-grade-filter-container.children"]
    cb_gvh_update_gvh_main_graph["update_gvh_main_graph<br><i>gvh.py</i>"]:::light
    data_store_gvh --> cb_gvh_update_gvh_main_graph
    cb_gvh_update_gvh_main_graph --> out_gvh_main_graph["gvh-main-graph.children"]
    cb_gvh_gvh_missing_summary_callback["gvh_missing_summary_callback<br><i>gvh.py</i>"]:::light
    data_store --> cb_gvh_gvh_missing_summary_callback
    cb_gvh_gvh_missing_summary_callback --> out_gvh_missing_summary_table["gvh-missing-summary-table.children"]
    cb_gvh_gvh_missing_detail_callback["gvh_missing_detail_callback<br><i>gvh.py</i>"]:::heavy
    data_store --> cb_gvh_gvh_missing_detail_callback
    cb_gvh_gvh_missing_detail_callback --> out_gvh_missing_detail_table["gvh-missing-detail-table.children"]
    cb_gvh_gvh_missing_detail_callback --> out_export_missing_gvh_button["export-missing-gvh-button.disabled"]
    cb_gvh_gvh_missing_detail_callback --> out_gvh_missing_store["gvh-missing-store.data"]
    cb_hemopathies_update_simple_barplot["update_simple_barplot<br><i>hemopathies.py</i>"]:::light
    data_store --> cb_hemopathies_update_simple_barplot
    cb_hemopathies_update_simple_barplot --> out_hemopathies_barplot_simple["hemopathies-barplot-simple.children"]
    cb_hemopathies_update_normalized_barplot["update_normalized_barplot<br><i>hemopathies.py</i>"]:::light
    data_store --> cb_hemopathies_update_normalized_barplot
    cb_hemopathies_update_normalized_barplot --> out_hemopathies_barplot_normalized["hemopathies-barplot-normalized.children"]
    cb_hemopathies_update_performance_scores_boxplot["update_performance_scores_boxplot<br><i>hemopathies.py</i>"]:::light
    data_store --> cb_hemopathies_update_performance_scores_boxplot
    cb_hemopathies_update_performance_scores_boxplot --> out_hemopathies_performance_scores_boxplot["hemopathies-performance-scores-boxplot.children"]
    cb_hemopathies_update_hemopathies_datatable["update_hemopathies_datatable<br><i>hemopathies.py</i>"]:::light
    data_store --> cb_hemopathies_update_hemopathies_datatable
    cb_hemopathies_update_hemopathies_datatable --> out_hemopathies_datatable["hemopathies-datatable.children"]
    cb_hemopathies_hemopathies_missing_summary_callback["hemopathies_missing_summary_callback<br><i>hemopathies.py</i>"]:::light
    data_store --> cb_hemopathies_hemopathies_missing_summary_callback
    cb_hemopathies_hemopathies_missing_summary_callback --> out_hemopathies_missing_summary_table["hemopathies-missing-summary-table.children"]
    cb_hemopathies_hemopathies_missing_detail_callback["hemopathies_missing_detail_callback<br><i>hemopathies.py</i>"]:::heavy
    data_store --> cb_hemopathies_hemopathies_missing_detail_callback
    cb_hemopathies_hemopathies_missing_detail_callback --> out_hemopathies_missing_detail_table["hemopathies-missing-detail-table.children"]
    cb_hemopathies_hemopathies_missing_detail_callback --> out_export_missing_hemopathies_button["export-missing-hemopathies-button.disabled"]
    cb_hemopathies_hemopathies_missing_detail_callback --> out_hemopathies_missing_store["hemopathies-missing-store.data"]
    cb_home_update_home_content["update_home_content<br><i>home.py</i>"]:::light
    data_store --> cb_home_update_home_content
    cb_home_update_home_content --> out_home_main_content["home-main-content.children"]
    cb_indics_update_indicator_content["update_indicator_content<br><i>indics.py</i>"]:::light
    data_store --> cb_indics_update_indicator_content
    cb_indics_update_indicator_content --> out_indicator_content["indicator-content.children"]
    cb_indics_indicators_missing_summary_callback["indicators_missing_summary_callback<br><i>indics.py</i>"]:::light
    data_store --> cb_indics_indicators_missing_summary_callback
    cb_indics_indicators_missing_summary_callback --> out_indicators_missing_summary_table["indicators-missing-summary-table.children"]
    cb_indics_indicators_missing_detail_callback["indicators_missing_detail_callback<br><i>indics.py</i>"]:::heavy
    data_store --> cb_indics_indicators_missing_detail_callback
    cb_indics_indicators_missing_detail_callback --> out_indicators_missing_detail_table["indicators-missing-detail-table.children"]
    cb_indics_indicators_missing_detail_callback --> out_export_missing_indicators_button["export-missing-indicators-button.disabled"]
    cb_indics_indicators_missing_detail_callback --> out_indicators_missing_store["indicators-missing-store.data"]
    cb_indics_indicators_missing_detail_callback --> out_indicators_name_store["indicators-name-store.data"]
    cb_patients_update_normalized_chart["update_normalized_chart<br><i>patients.py</i>"]:::light
    data_store_viz --> cb_patients_update_normalized_chart
    cb_patients_update_normalized_chart --> out_patients_normalized_chart["patients-normalized-chart.children"]
    cb_patients_update_distribution_chart["update_distribution_chart<br><i>patients.py</i>"]:::light
    data_store_viz --> cb_patients_update_distribution_chart
    cb_patients_update_distribution_chart --> out_patients_distribution_chart["patients-distribution-chart.children"]
    cb_patients_update_boxplot_chart["update_boxplot_chart<br><i>patients.py</i>"]:::light
    data_store_viz --> cb_patients_update_boxplot_chart
    cb_patients_update_boxplot_chart --> out_patients_boxplot_chart["patients-boxplot-chart.children"]
    cb_patients_update_datatable["update_datatable<br><i>patients.py</i>"]:::light
    data_store --> cb_patients_update_datatable
    cb_patients_update_datatable --> out_patients_datatable["patients-datatable.children"]
    cb_patients_update_datatable --> out_export_csv_button["export-csv-button.disabled"]
    cb_patients_update_datatable --> out_patients_stats_store["patients-stats-store.data"]
    cb_patients_update_patients_performance_scores_boxplot["update_patients_performance_scores_boxplot<br><i>patients.py</i>"]:::light
    data_store_viz --> cb_patients_update_patients_performance_scores_boxplot
    cb_patients_update_patients_performance_scores_boxplot --> out_patients_performance_scores_boxplot["patients-performance-scores-boxplot.children"]
    cb_patients_patients_missing_summary_callback["patients_missing_summary_callback<br><i>patients.py</i>"]:::light
    data_store --> cb_patients_patients_missing_summary_callback
    cb_patients_patients_missing_summary_callback --> out_patients_missing_summary_table["patients-missing-summary-table.children"]
    cb_patients_patients_missing_detail_callback["patients_missing_detail_callback<br><i>patients.py</i>"]:::heavy
    data_store --> cb_patients_patients_missing_detail_callback
    cb_patients_patients_missing_detail_callback --> out_patients_missing_detail_table["patients-missing-detail-table.children"]
    cb_patients_patients_missing_detail_callback --> out_export_missing_patients_button["export-missing-patients-button.disabled"]
    cb_patients_patients_missing_detail_callback --> out_patients_missing_store["patients-missing-store.data"]
    cb_procedures_update_main_variable_options["update_main_variable_options<br><i>procedures.py</i>"]:::light
    data_store --> cb_procedures_update_main_variable_options
    cb_procedures_update_main_variable_options --> out_procedures_main_variable_integrated["procedures-main-variable-integrated.options"]
    cb_procedures_update_main_variable_options --> out_procedures_main_variable_integrated["procedures-main-variable-integrated.value"]
    cb_procedures_update_main_chart["update_main_chart<br><i>procedures.py</i>"]:::light
    data_store --> cb_procedures_update_main_chart
    cb_procedures_update_main_chart --> out_procedures_main_chart["procedures-main-chart.children"]
    cb_procedures_update_cmv_charts["update_cmv_charts<br><i>procedures.py</i>"]:::light
    data_store --> cb_procedures_update_cmv_charts
    cb_procedures_update_cmv_charts --> out_procedures_cmv_charts["procedures-cmv-charts.children"]
    cb_procedures_update_aplasia_tab_content["update_aplasia_tab_content<br><i>procedures.py</i>"]:::light
    data_store --> cb_procedures_update_aplasia_tab_content
    cb_procedures_update_aplasia_tab_content --> out_procedures_aplasia_tab_content["procedures-aplasia-tab-content.children"]
    cb_procedures_update_treatment_chart["update_treatment_chart<br><i>procedures.py</i>"]:::heavy
    data_store --> cb_procedures_update_treatment_chart
    cb_procedures_update_treatment_chart --> out_procedures_treatment_content["procedures-treatment-content.children"]
    cb_procedures_update_prophylaxis_chart["update_prophylaxis_chart<br><i>procedures.py</i>"]:::heavy
    data_store --> cb_procedures_update_prophylaxis_chart
    cb_procedures_update_prophylaxis_chart --> out_procedures_prophylaxis_content["procedures-prophylaxis-content.children"]
    cb_procedures_procedures_missing_summary_callback["procedures_missing_summary_callback<br><i>procedures.py</i>"]:::light
    data_store --> cb_procedures_procedures_missing_summary_callback
    cb_procedures_procedures_missing_summary_callback --> out_procedures_missing_summary_table["procedures-missing-summary-table.children"]
    cb_procedures_procedures_missing_detail_callback["procedures_missing_detail_callback<br><i>procedures.py</i>"]:::heavy
    data_store --> cb_procedures_procedures_missing_detail_callback
    cb_procedures_procedures_missing_detail_callback --> out_procedures_missing_detail_table["procedures-missing-detail-table.children"]
    cb_procedures_procedures_missing_detail_callback --> out_export_missing_procedures_button["export-missing-procedures-button.disabled"]
    cb_procedures_procedures_missing_detail_callback --> out_procedures_missing_store["procedures-missing-store.data"]
    cb_relapse_update_relapse_main_graph["update_relapse_main_graph<br><i>relapse.py</i>"]:::light
    data_store --> cb_relapse_update_relapse_main_graph
    cb_relapse_update_relapse_main_graph --> out_relapse_main_graph["relapse-main-graph.children"]
    cb_relapse_relapse_missing_summary_callback["relapse_missing_summary_callback<br><i>relapse.py</i>"]:::light
    data_store --> cb_relapse_relapse_missing_summary_callback
    cb_relapse_relapse_missing_summary_callback --> out_relapse_missing_summary_table["relapse-missing-summary-table.children"]
    cb_relapse_relapse_missing_detail_callback["relapse_missing_detail_callback<br><i>relapse.py</i>"]:::heavy
    data_store --> cb_relapse_relapse_missing_detail_callback
    cb_relapse_relapse_missing_detail_callback --> out_relapse_missing_detail_table["relapse-missing-detail-table.children"]
    cb_relapse_relapse_missing_detail_callback --> out_export_missing_relapse_button["export-missing-relapse-button.disabled"]
    cb_relapse_relapse_missing_detail_callback --> out_relapse_missing_store["relapse-missing-store.data"]
    cb_survival_update_gvh_filters_container["update_gvh_filters_container<br><i>survival.py</i>"]:::light
    data_store --> cb_survival_update_gvh_filters_container
    cb_survival_update_gvh_filters_container --> out_survival_gvh_filters_container["survival-gvh-filters-container.children"]
    cb_survival_update_global_survival_curve["update_global_survival_curve<br><i>survival.py</i>"]:::heavy
    data_store_survival --> cb_survival_update_global_survival_curve
    cb_survival_update_global_survival_curve --> out_survival_global_curve["survival-global-curve.children"]
    cb_survival_update_survival_curves_by_year["update_survival_curves_by_year<br><i>survival.py</i>"]:::heavy
    data_store_survival --> cb_survival_update_survival_curves_by_year
    cb_survival_update_survival_curves_by_year --> out_survival_curves_by_year["survival-curves-by-year.children"]
    cb_survival_update_survival_curves_by_year --> out_survival_stats_table["survival-stats-table.children"]
    cb_survival_update_survival_grfs_graph["update_survival_grfs_graph<br><i>survival.py</i>"]:::heavy
    data_store_survival --> cb_survival_update_survival_grfs_graph
    cb_survival_update_survival_grfs_graph --> out_survival_grfs_graph["survival-grfs-graph.children"]
    cb_survival_update_survival_grfs_graph --> out_survival_grfs_curves_by_year["survival-grfs-curves-by-year.children"]
    cb_survival_update_survival_grfs_graph --> out_survival_grfs_stats_table["survival-grfs-stats-table.children"]
    cb_survival_survival_missing_summary_callback["survival_missing_summary_callback<br><i>survival.py</i>"]:::light
    data_store --> cb_survival_survival_missing_summary_callback
    cb_survival_survival_missing_summary_callback --> out_survival_missing_summary_table["survival-missing-summary-table.children"]
    cb_survival_survival_missing_detail_callback["survival_missing_detail_callback<br><i>survival.py</i>"]:::heavy
    data_store --> cb_survival_survival_missing_detail_callback
    cb_survival_survival_missing_detail_callback --> out_survival_missing_detail_table["survival-missing-detail-table.children"]
    cb_survival_survival_missing_detail_callback --> out_export_missing_survival_button["export-missing-survival-button.disabled"]
    cb_survival_survival_missing_detail_callback --> out_survival_missing_store["survival-missing-store.data"]
    cb_toxicity_update_toxicity_nrm_graph["update_toxicity_nrm_graph<br><i>toxicity.py</i>"]:::light
    data_store --> cb_toxicity_update_toxicity_nrm_graph
    cb_toxicity_update_toxicity_nrm_graph --> out_toxicity_nrm_graph["toxicity-nrm-graph.children"]
    cb_toxicity_toxicity_missing_summary_callback["toxicity_missing_summary_callback<br><i>toxicity.py</i>"]:::light
    data_store --> cb_toxicity_toxicity_missing_summary_callback
    cb_toxicity_toxicity_missing_summary_callback --> out_toxicity_missing_summary_table["toxicity-missing-summary-table.children"]
    cb_toxicity_toxicity_missing_detail_callback["toxicity_missing_detail_callback<br><i>toxicity.py</i>"]:::heavy
    data_store --> cb_toxicity_toxicity_missing_detail_callback
    cb_toxicity_toxicity_missing_detail_callback --> out_toxicity_missing_detail_table["toxicity-missing-detail-table.children"]
    cb_toxicity_toxicity_missing_detail_callback --> out_export_missing_toxicity_button["export-missing-toxicity-button.disabled"]
    cb_toxicity_toxicity_missing_detail_callback --> out_toxicity_missing_store["toxicity-missing-store.data"]

    classDef heavy fill:#f8d7da,stroke:#c0392b;
    classDef light fill:#d4edda,stroke:#2e7d32;
```

---

## Analyse (rédigée, à conserver si le rapport est régénéré)

### Verdict sur les hypothèses

- **H1 confirmée.** 46/73 callbacks reçoivent un store de données en `Input` ; 38 reçoivent le **dataset complet** (`data-store`). À chaque déclenchement, le navigateur renvoie le JSON complet (~14,5 Mo sérialisé par store sur le jeu synthétique, ~57 Mo constatés en production avec plusieurs stores dans le payload) et le serveur le redécode.
- **H3 confirmée.** Chaque page rend ses composants dynamiquement dans `main-content` ; les callbacks de la page ont `current-page.data` + `data-store.data` en `Input` **sans** `prevent_initial_call=True` (46 callbacks dans ce cas). À l'arrivée sur une page, **tous** ses callbacks partent en rafale, chacun avec le dataset complet en pièce jointe. C'est ce qui produit les ~20 requêtes `_dash-update-component` par changement d'onglet.
- Le `navigate` global (`app.py:150`) a **`data-store` en `Input` alors qu'il n'utilise que `data is None`** (activer/désactiver les boutons) : chaque clic de navigation envoie le dataset complet au serveur pour un booléen. Même motif dans `toggle_sidebar_visibility` (`app.py:444`) et `toggle_purge_button_visibility` (`app.py:717`).

### Requêtes par changement d'onglet (décompte attendu)

| Page | Callbacks avec store en Input déclenchés au rendu | Stores utilisés |
|---|---|---|
| Patients | 6 (3 graphiques `viz` + datatable + 2 missing) | viz ×3, complet ×3 |
| Indications (hemopathies) | 6 (4 graphiques + 2 missing) | complet ×6 |
| Procedures | 8 (options, main, CMV, aplasie, conditionnement, prophylaxie + 2 missing) | complet ×8 |
| GvH | 4 (filtres grade + graphe principal `gvh` + 2 missing) | gvh ×1, complet ×3 |
| Relapse / Toxicity | 3 chacune (graphe + 2 missing) | complet ×3 |
| Survival | 6 (conteneur filtres + 3 courbes `survival` + 2 missing) | survival ×3, complet ×3 |
| Indicators | 3 (contenu + 2 missing) | complet ×3 |
| + app.py | `navigate`, `update_sidebar`, `toggle_sidebar_visibility`, `toggle_purge_button_visibility`, `update_main_content` | complet ×4 |

### Redondances repérées

1. **Missing data** : sur chaque page, `*_missing_summary_callback` et `*_missing_detail_callback` se déclenchent tous les deux au rendu et à chaque filtre, tous deux sur le `data-store` complet, alors que la page dispose souvent d'un slim store. Les callbacks `detail` font un `iterrows` (`gvh.py:575`, `hemopathies.py:935`, `indics.py:4122`, `patients.py:1108`, `procedures.py:1015`, `relapse.py:561`, `survival.py:2329`, `toxicity.py:576`).
2. **Pages hétérogènes** : `patients` et `survival` utilisent bien les slim stores (`data-store-viz`, `data-store-survival`) pour leurs graphiques, mais `hemopathies`, `procedures`, `relapse`, `toxicity`, `gvh` (filtres + missing) et `indics` consomment le `data-store` complet même pour des agrégations simples.
3. **Même filtrage refait N fois** : sur une page, chaque callback ré-applique indépendamment les mêmes filtres (année, âge, malignité) sur le même dataset décodé N fois.

### Candidats `Input` → `State` (phase 4)

- `app.py` : `data-store` dans `navigate`, `toggle_sidebar_visibility`, `toggle_purge_button_visibility` (seule la présence des données compte → un `metadata-store` léger ou `State` suffit).
- Toutes les pages : `data-store*` pourrait passer en `State` avec un déclencheur explicite de version (« data-version ») — les données ne changent qu'à l'upload/purge, pas aux filtres.
- `update_sidebar` (`app.py:243`) n'a besoin que des années/valeurs de filtres, pas du dataset complet.

### À valider par la mesure manuelle (devtools Dash)

Le décompte exact et la taille de chaque requête par changement d'onglet restent à relever dans le panneau « Callbacks » (section 6, phase 1 du plan) pour confirmer que la rafale correspond au décompte ci-dessus.
