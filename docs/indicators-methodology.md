# Indicator Calculation Methodology

### Technical Architecture

The **AlloGraph** application is developed in Python (v3.10) using the **Dash** framework (v2.18.2) for the web interface and **Plotly** (v5.17.0) for interactive visualizations. The indicator analysis module is implemented in the `pages/indics.py` file and relies on the **Pandas** (v2.1.4) and **NumPy** (v1.24.3) libraries for data processing.

---

### Data Preprocessing

Before any indicator calculation, the raw data (EBMT/REDCap format) undergoes standardized preprocessing (`modules/data_processing.py`):

| Transformation | Description |
|----------------|-------------|
| **Column normalization** | Case-insensitive conversion of column names |
| **Age calculation** | `Age At Diagnosis` = (Date Diagnosis - Date Of Birth) / 365.25 |
| **Age groups** | Categorization: 18-, 18-39, 40-64, 65-74, 75+ |
| **Diagnostic category** | Malignant/Non-malignant classification based on Main Diagnosis |
| **Derived variables** | Creation of `Donor Match Category` (Genoidentical, MRD, MUD, MMUD) |
| **cGVH transformation** | Recoding: Limited→Mild, Extensive→Severe |

---

### Methodology by Indicator

#### Acute Graft-versus-Host Disease (aGVH)

**Function**: `process_gvha_data()`  
**Required variables**: `First Agvhd Occurrence Date`, `Treatment Date`, `First aGvHD Maximum Score`

**Calculation method**:
```
aGVH delay = First Agvhd Occurrence Date - Treatment Date (in days)

Inclusion: Delay ≤ 100 days AND Grade ∈ {Grade 2, Grade 3, Grade 4}

Results:
- aGVH Grades 2-4: Number of patients with Grade 2, 3 or 4
- aGVH Grades 3-4: Number of patients with Grade 3 or 4

aGvH rate (%) = (Number of cases / Total number of transplants) × 100
```

**Visualization**: Stacked barplot by grade (2, 3, 4) with a distinct color for each grade.

---

#### 2. Chronic Graft-versus-Host Disease (cGVH)

**Function**: `process_gvhc_data()`  
**Required variables**: `First Cgvhd Occurrence Date`, `Treatment Date`, `First cGvHD Maximum NIH Score`

**Calculation method**:
```
cGVH delay = First Cgvhd Occurrence Date - Treatment Date (in days)

Inclusion: Delay ≤ 365 days AND Score ∈ {Mild, Moderate, Severe}

Prior transformation:
- Limited → Mild
- Extensive → Severe

Results stratified by grade (Mild, Moderate, Severe)
cGvH rate (%) = (Number of cases / Total number of transplants) × 100
```

---

#### 3. TRM (Toxicity-Related Mortality)

**Function**: `process_trm_data()`  
**Required variables**: `Status Last Follow Up`, `Death Cause`, `Date Of Last Follow Up`, `Treatment Date`

**Calculation method**:
```
Follow-up days = Date Of Last Follow Up - Treatment Date

Inclusion filter:
- Death Cause ∈ {'Cellular therapy-related cause of death', 'HCT-related cause of death'}
- AND (Status = 'Dead' OR (Status = 'Alive' AND Follow-up days ≥ 365))

TRM D30 = Death with Follow-up days ≤ 30
TRM D100 = Death with Follow-up days ≤ 100  
TRM D365 = Death with Follow-up days ≤ 365

TRM rate (%) = (Number of TRM deaths / Total number of transplants) × 100
```

**Visualization**: Curve with points at D30, D100, D365.

---

#### 4. Overall Survival

**Function**: `process_survie_data()`  
**Required variables**: `Status Last Follow Up`, `Date Of Last Follow Up`, `Treatment Date`

**Calculation method**:
```
Inclusion filter:
- Status ∈ {'Dead', 'Died after conditioning but before main treatment'}
- OR (Status = 'Alive' AND Follow-up days ≥ 365)

Death D30 = Death with Follow-up days ≤ 30
Death D100 = Death with Follow-up days ≤ 100
Death D365 = Death with Follow-up days ≤ 365

Survivors = Total - Deaths
Survival rate (%) = (Survivors / Total) × 100
```

**Visualization**: Curve with points at D30, D100, D365.

---

#### 5. Transplantation Success

**Function**: `process_prise_greffe_data()`  
**Required variables**: `Date Platelet Reconstitution`, `Treatment Date`

**Calculation method**:
```
Reconstitution delay = Date Platelet Reconstitution - Treatment Date (days)

Inclusion: Non-missing data AND Delay ≤ 100 days

Success = Number of patients with reconstitution ≤ 100 days
Success rate (%) = (Success / Total number with valid data) × 100

```

**Visualization**: Barplot with an 80% threshold.

---

#### 6. ANC Recovery

**Function**: `process_sortie_aplasie_data()`  
**Required variables**: `Date Anc Recovery`, `Treatment Date`

**Calculation method**:
```
ANC reconstitution delay = Date Anc Recovery - Treatment Date (days)

Inclusion: Non-missing data AND Delay ≤ 28 days

Success = Number of patients with ANC reconstitution ≤ 28 days
ANC recovery rate (%) = (Success / Total number with valid data) × 100
```

**Visualization**: Barplot with an 80% threshold.

---

#### 7. Relapse

**Function**: `process_rechute_data()`  
**Required variables**: `First Relapse`, `First Relapse Date`, `Treatment Date`

**Calculation method**:
```
Conversion: First Relapse = "Yes" → 1, otherwise → 0

Relapse delay = First Relapse Date - Treatment Date (days)

Inclusion: Date data available

Relapse D100 = First Relapse = "Yes" AND Delay ≤ 100 days
Relapse D365 = First Relapse = "Yes" AND Delay ≤ 365 days

Relapse rate (%) = (Number of relapses / Total number with valid data) × 100
```

**Visualization**: Curve with points at D100, D365.

---

### Competing Risks Analysis

For GvH and relapse analyses that account for death as a competing event, the `CompetingRisksAnalyzer` class (`modules/competing_risks.py`) implements:

```python
# Gray's method for cumulative incidence
hazard = N events / N at risk
Cumulative incidence(t) = Σ [Survival(t-1) × hazard(t)]
```

**Events considered**:
- Event of interest (GvH or relapse)
- Death as a competing risk
- Censoring at the date of last follow-up

---
### Missing Data Handling

The `analyze_missing_data()` method distinguishes:
1. **Truly missing data**: Empty field with no additional information
2. **Non-applicable data**: For example, absence of GvH with a follow-up date filled in = "No GvH" (not missing)
