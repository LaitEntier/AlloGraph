# Data format

AlloGraph expects data compatible with the **EBMT Registry** export structure: one row per transplant, columns as listed below. Upload accepts **CSV** (separator auto-detected: `,` `;` tab `|`) and **Excel** (`.xlsx`, `.xls`).

`data/import_template_allograph.xlsx` is the canonical template, and `data/test_sample.csv` is a de-identified example.

## Column name matching

Matching is **case-insensitive**: `treatment date`, `Treatment Date`, and `TREATMENT DATE` all map to `Treatment Date`. A few known synonyms are also handled (e.g. `Match Type Related Donor` → `Match Type`). The authoritative list is `EXPECTED_COLUMNS` in `modules/data_processing.py`.

## Expected columns

### Identification & demographics

| Column | Description |
|---|---|
| `Long ID` | Patient identifier |
| `Short ID` | Short identifier |
| `Promise ID` | PROMISE registry identifier |
| `Sex` | Patient sex |
| `Date Of Birth` | Birth date |
| `Blood Group` | ABO group |
| `Rhesus Factor` | Rh factor |
| `Initials First Name` / `Initials Last Name` | Patient initials |

### Diagnosis

| Column | Description |
|---|---|
| `Date Diagnosis` | Diagnosis date |
| `Main Diagnosis` | Primary disease |
| `Subclass Diagnosis` | Disease subclassification |

### Transplant procedure

| Column | Description |
|---|---|
| `Treatment CIC` | Transplant center |
| `Treatment Type` | Type of treatment |
| `Treatment Date` | Transplant date (drives the derived `Year`) |
| `Number HCT` / `Number Allo HCT` | Transplant numbering |
| `Performance Status At Treatment Scale` | Scale used (ECOG / Karnofsky / Lansky) |
| `Performance Status At Treatment Score` | Score at transplant |
| `Disease Status At Treatment` | Disease status at transplant |
| `CMV Status Donor` / `CMV Status Patient` | CMV serology |
| `Donor Type` | Donor category |
| `Source Stem Cells` / `Source Stem Cells 2` | Graft source |
| `Match Type` | Donor–recipient match |
| `Conditioning Regimen Type` | Myeloablative / reduced-intensity… |
| `Prep Regimen …` | One column per agent: `Bendamustine`, `Busulfan`, `Cyclophosphamide`, `Fludarabine`, `Melphalan`, `Thiotepa`, `Treosulfan` |
| `Prophylaxis` / `Prophylaxis Drug 1–6` | GvHD prophylaxis regimen |
| `TBI` / `TBI Dose Gray` | Total body irradiation |

### Follow-up & outcomes

| Column | Description |
|---|---|
| `Date Of Last Follow Up` | Last follow-up date |
| `Status Last Follow Up` | `Dead` / `Alive` |
| `Death Cause` / `Death Date` | Death information |
| `First aGvHD Maximum Score` / `First Agvhd Occurrence` / `First Agvhd Occurrence Date` | Acute GvHD |
| `First cGvHD Maximum NIH Score` / `First Cgvhd Occurrence` / `First Cgvhd Occurrence Date` | Chronic GvHD |
| `First Relapse` / `First Relapse Date` | Relapse |
| `First Best Response` / `First Best Response Date` | Best response |
| `Platelet Reconstitution` / `Date Platelet Reconstitution` | Platelet recovery |
| `Anc Recovery` / `Date Anc Recovery` | Neutrophil recovery |
| `Date Subsequent Treatment` | Subsequent treatment |
| `Performance Scale At Last FU` / `Performance Score At Last FU` | Performance at last follow-up |
| `Cgvhd Maximum Nih Score At Last Fu` / `Cgvhd Occurrence At Last Fu` | Chronic GvHD at last follow-up |

## Derived variables

`process_data()` adds: `Year`, `Age At Diagnosis`, `Age Groups`, `Greffes`, `Blood + Rh`, `Compatibilité HLA`, `Main Diagnosis Category`, binary indicators for conditioning/prophylaxis agents, and remapped chronic GvHD scores. See [Architecture](../getting-started/architecture.md#key-data-transformations) for details.

!!! warning "Sensitive data"
    These files contain patient data. Everything is processed in memory and stored client-side only (see [Deployment](../deployment.md#security-gdpr)) — never commit real patient files to the repository. `data/test_sample.csv` is de-identified and safe.
