# Méthodologie de calcul des indicateurs

### Architecture Technique

L'application **AlloGraph** est développée en Python (v3.10) utilisant le framework **Dash** (v2.18.2) pour l'interface web et **Plotly** (v5.17.0) pour les visualisations interactives. Le module d'analyse des indicateurs est implémenté dans le fichier `pages/indics.py` et repose sur les bibliothèques **Pandas** (v2.1.4) et **NumPy** (v1.24.3) pour le traitement des données.

---

### Traitement Préalable des Données

Avant tout calcul d'indicateurs, les données brutes (format EBMT/REDCap) subissent un prétraitement standardisé (`modules/data_processing.py`) :

| Transformation | Description |
|----------------|-------------|
| **Normalisation des colonnes** | Conversion insensible à la casse des noms de colonnes |
| **Calcul de l'âge** | `Age At Diagnosis` = (Date Diagnosis - Date Of Birth) / 365.25 |
| **Tranches d'âge** | Catégorisation : 18-, 18-39, 40-64, 65-74, 75+ |
| **Catégorie diagnostique** | Classification Malignant/Non-malignant selon Main Diagnosis |
| **Variables dérivées** | Création de `Donor Match Category` (Genoidentical, MRD, MUD, MMUD) |
| **Transformation GVHc** | Recodage : Limited→Mild, Extensive→Severe |

---

### Méthodologie par Indicateur

#### Graft-versus-Host Disease Aiguë (aGVH)

**Fonction** : `process_gvha_data()`  
**Variables requises** : `First Agvhd Occurrence Date`, `Treatment Date`, `First aGvHD Maximum Score`

**Méthode de calcul** :
```
Délai aGVH = First Agvhd Occurrence Date - Treatment Date (en jours)

Inclusion : Délai ≤ 100 jours ET Grade ∈ {Grade 2, Grade 3, Grade 4}

Résultats :
- aGVH Grades 2-4 : Nombre de patients avec Grade 2, 3 ou 4
- aGVH Grades 3-4 : Nombre de patients avec Grade 3 ou 4

Taux GvHa (%) = (Nombre de cas / Nombre total de greffes) × 100
```

**Visualisation** : Barplot empilé par grade (2, 3, 4) avec coloration distincte selon grade.

---

#### 2. Graft-versus-Host Disease Chronique (cGVH)

**Fonction** : `process_gvhc_data()`  
**Variables requises** : `First Cgvhd Occurrence Date`, `Treatment Date`, `First cGvHD Maximum NIH Score`

**Méthode de calcul** :
```
Délai cGVH = First Cgvhd Occurrence Date - Treatment Date (en jours)

Inclusion : Délai ≤ 365 jours ET Score ∈ {Mild, Moderate, Severe}

Transformation préalable :
- Limited → Mild
- Extensive → Severe

Résultats stratifiés par grade (Mild, Moderate, Severe)
Taux GvHc (%) = (Nombre de cas / Nombre total de greffes) × 100
```

---

#### 3. TRM (Toxicity-Related Mortality / Mortalité liée à la toxicité)

**Fonction** : `process_trm_data()`  
**Variables requises** : `Status Last Follow Up`, `Death Cause`, `Date Of Last Follow Up`, `Treatment Date`

**Méthode de calcul** :
```
Follow-up days = Date Of Last Follow Up - Treatment Date

Filtre d'inclusion :
- Death Cause ∈ {'Cellular therapy-related cause of death', 'HCT-related cause of death'}
- ET (Status = 'Dead' OU (Status = 'Alive' ET Follow-up days ≥ 365))

TRM J30 = Décès avec Follow-up days ≤ 30
TRM J100 = Décès avec Follow-up days ≤ 100  
TRM J365 = Décès avec Follow-up days ≤ 365

Taux TRM (%) = (Nombre de décès TRM / Nombre total de greffes) × 100
```

**Visualisation** : Courbe avec points à D30, D100, D365.

---

#### 4. Survie Globale (Overall Survival)

**Fonction** : `process_survie_data()`  
**Variables requises** : `Status Last Follow Up`, `Date Of Last Follow Up`, `Treatment Date`

**Méthode de calcul** :
```
Filtre d'inclusion :
- Status ∈ {'Dead', 'Died after conditioning but before main treatment'}
- OU (Status = 'Alive' ET Follow-up days ≥ 365)

Décès J30 = Décès avec Follow-up days ≤ 30
Décès J100 = Décès avec Follow-up days ≤ 100
Décès J365 = Décès avec Follow-up days ≤ 365

Survivants = Total - Décès
Taux de survie (%) = (Survivants / Total) × 100
```

**Visualisation** : Courbe avec points à D30, D100, D365.

---

#### 5. Prise de Greffe (Transplantation Success)

**Fonction** : `process_prise_greffe_data()`  
**Variables requises** : `Date Platelet Reconstitution`, `Treatment Date`

**Méthode de calcul** :
```
Délai reconstitution = Date Platelet Reconstitution - Treatment Date (jours)

Inclusion : Données non manquantes ET Délai ≤ 100 jours

Succès = Nombre de patients avec reconstitution ≤ 100 jours
Taux de succès (%) = (Succès / Nombre total avec données valides) × 100

```

**Visualisation** : Barplot avec seuil à 80%.

---

#### 6. Sortie d'Aplasie (ANC Recovery / Reconstitution neutrophile)

**Fonction** : `process_sortie_aplasie_data()`  
**Variables requises** : `Date Anc Recovery`, `Treatment Date`

**Méthode de calcul** :
```
Délai reconstitution ANC = Date Anc Recovery - Treatment Date (jours)

Inclusion : Données non manquantes ET Délai ≤ 28 jours

Succès = Nombre de patients avec reconstitution ANC ≤ 28 jours
Taux de sortie d'aplasie (%) = (Succès / Nombre total avec données valides) × 100
```

**Visualisation** : Barplot avec seuil à 80%.

---

#### 7. Rechute (Relapse)

**Fonction** : `process_rechute_data()`  
**Variables requises** : `First Relapse`, `First Relapse Date`, `Treatment Date`

**Méthode de calcul** :
```
Conversion : First Relapse = "Yes" → 1, sinon → 0

Délai rechute = First Relapse Date - Treatment Date (jours)

Inclusion : Données de date disponibles

Rechute J100 = First Relapse = "Yes" ET Délai ≤ 100 jours
Rechute J365 = First Relapse = "Yes" ET Délai ≤ 365 jours

Taux de rechute (%) = (Nombre de rechutes / Nombre total avec données valides) × 100
```

**Visualisation** : Courbe avec points à D100, D365.

---

### Analyse des Risques Compétitifs

Pour les analyses de GvH et rechute avec prise en compte du décès comme événement compétitif, la classe `CompetingRisksAnalyzer` (`modules/competing_risks.py`) implémente :

```python
# Méthode de Gray pour l'incidence cumulée
hazard = N événements / N à risque
Incidence cumulée(t) = Σ [Survie(t-1) × hazard(t)]
```

**Événements pris en compte** :
- Événement d'intérêt (GvH ou rechute)
- Décès comme risque compétitif
- Censure à la date de dernier suivi

---
### Gestion des Données Manquantes

La méthode `analyze_missing_data()` distingue :
1. **Données véritablement manquantes** : Champ vide sans information complémentaire
2. **Données non applicables** : Par exemple, absence de GvH avec date de suivi renseignée = "Pas de GvH" (non manquant)