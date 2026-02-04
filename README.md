# AlloGraph

## Overview

AlloGraph is a comprehensive web-based application designed for the analysis of allogeneic hematopoietic stem cell transplantation data. Built primarily using the Dash and Plotly Python libraries, this application aims to provide clinicians and researchers with reproducible analytical tools that conform to the European Society for Blood and Marrow Transplantation (EBMT) registry data model.

## Purpose and Scope

This application addresses the critical need for standardized, interactive analysis tools in the field of hematopoietic stem cell transplantation. AlloGraph enables healthcare professionals to perform sophisticated statistical analyses on patient cohorts, including survival analysis, competing risks assessment, and comprehensive demographic studies.

## Analytical Modules

**Home Dashboard**
Provides an overview of loaded datasets with temporal distribution visualizations of transplant procedures by year.

**Patient Demographics Analysis**
Comprehensive demographic analysis including age group stratification, gender distribution, and baseline characteristics. The module includes interactive boxplots for performance score analysis and detailed statistical summaries by year.

**Hematological Disease Analysis**
Detailed examination of primary and secondary diagnoses with normalized distribution analyses. Features performance score stratification by age groups and comprehensive diagnostic classification tables.

**Procedural Analysis**
Analysis of transplantation procedures including donor type evolution, stem cell source distribution, and cytomegalovirus (CMV) status assessment for both donors and recipients. The module includes treatment prophylaxis analysis and conditioning regimen evaluation, along with aplasia and thrombocytopenia duration histograms.

**Graft-versus-Host Disease (GvHD) Analysis**
Competing risks analysis for both acute and chronic GvHD using established statistical methodologies. Provides cumulative incidence curves with appropriate risk adjustment.

**Relapse Analysis**
Comprehensive relapse risk assessment using competing risks methodology, analyzing relapse versus death as competing endpoints with temporal event tracking.

**Survival Analysis**
Kaplan-Meier survival analysis with both global and stratified approaches. Supports long-term follow-up analysis with configurable time horizons and provides detailed statistical summaries including confidence intervals and survival probabilities at key time points.

**Clinical Indicators**
Comprehensive dashboard of key performance indicators including treatment-related mortality (TRM) at 30, 100, and 365 days, overall survival metrics, engraftment rates at 100 days, neutrophil recovery at 28 days, relapse incidence at 100 and 365 days, as well as both acute and chronic GvHD indicators. All indicators are presented with modern label visualizations and temporal trend analysis.

## Technical Requirements

### System Prerequisites
- Python 3.10
- Package manager (pip or conda)

### Dependencies
The application requires several Python packages including Dash for web framework functionality, Plotly for interactive visualizations, Pandas for data manipulation, NumPy for numerical computations, SciPy for statistical analysis, and Lifelines for survival analysis (optional but recommended).

## Local Setup

### Application Launch
Download the latest release and execute the main application file using Python. The application will be accessible via web browser at the default localhost address on port 8050 (http://127.0.0.1:8050/).

## Data Format Requirements

The application is designed to work with datasets conforming to EBMT Registry standards. You may contact the EBMT and ask for a database extraction relative to your care facility.

## Application Architecture

The codebase follows a modular architecture with clear separation of concerns. The main application file coordinates the overall functionality, while individual page modules handle specific analytical domains. Utility modules provide data processing capabilities, layout components, and specialized statistical functions. The visualization module contains all graphing and chart generation functions.
