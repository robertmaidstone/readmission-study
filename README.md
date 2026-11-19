# Synthetic Healthcare Readmission Study

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/robertmaidstone/readmission-study?cacheSeconds=60)

## Overview

A reproducible, end-to-end healthcare analytics project built with **PostgreSQL, SQL, Python and Jupyter**. It generates realistic-but-synthetic patient and admission records, validates the data, loads it into a relational database, and performs exploratory readmission analysis.

> Synthetic data only. This project does not contain patient or clinical information and is for portfolio and learning purposes.

| Dataset | Size |
|---|---:|
| Synthetic patients | 1,000 |
| Synthetic admissions | 3,441 |
| Study period | 2019-01-01 - 2023-12-31 |

### Portfolio highlights

- Relational PostgreSQL data model with primary and foreign keys
- CSV data generation and 30-day readmission scenario rules
- Automated data-quality checks for IDs, dates, duplicate records, overlaps and diagnoses
- SQL-to-Pandas analytics workflow
- Demographic, length-of-stay and readmission visualisations
- Local credentials kept outside version control

---

## Project Structure

```text
readmission-study/

data/
    patients.csv
    admissions.csv

sql/
    schema.sql

src/
    generate_data.py
    load_data.py
    readmission_analysis.py
    validate_data.py

notebooks/
    analysis.ipynb

tests/
    test_readmission_analysis.py

requirements.txt
README.md
```

---

## Data Model

The synthetic dataset currently contains:

### Patients

| Variable | Description |
|-----------|-------------|
| patient_id | Unique patient identifier |
| dob | Date of birth of patient |
| sex | Biological sex |

### Admissions

| Variable | Description |
|-----------|-------------|
| admission_id | Unique admission identifier |
| patient_id | Linked patient identifier |
| admission_date | Admission date |
| discharge_date | Discharge date |
| diagnosis | Primary diagnosis |
| readmission_reason | Event category relative to the preceding discharge |

### Synthetic admission assumptions

Admissions are written in chronological order. Each patient's next admission starts at least one day after the previous discharge, so stays do not overlap. Data is generated on a generation from 2018–2024, then admissions are censored by admission date to the study window of 2019-01-01 through 2023-12-31, this aims to better simulate real data where patients admissions exist beyond the study window. A patient's first retained admission is marked as `index_admission`; admissions outside the study window are not included in `admissions.csv`.

`readmission_reason` is assigned to the admission that follows the preceding discharge:

| Value | Meaning |
|-------|---------|
| `index_admission` | Patient's first generated admission |
| `unplanned_related` | Same diagnosis, 1–30 days after the previous discharge |
| `unplanned_unrelated` | Different diagnosis, 1–30 days after the previous discharge |
| `planned_follow_up` | Planned return with the same diagnosis, 1–30 days after discharge |
| `new_episode` | New episode, 31–365 days after the previous discharge |

The generator uses illustrative weights of 15/10/10/65 for the four subsequent-admission categories. These are synthetic scenario settings, not estimates of real-world rates. A 30-day all-cause readmission measure includes planned and unplanned returns; an unplanned measure should include only the two `unplanned_*` categories.

Future versions could incorporate:

- Comorbidity burden
- Secondary diagnoses and procedures
- Medication records
- Mortality outcomes
- Discharge destination

---

## Workflow

```text
Synthetic Data Generation
            ↓
      PostgreSQL
            ↓
      SQL Queries
            ↓
      Python/Pandas
            ↓
 Visualisation & Modelling
            ↓
 Jupyter Notebook Report
```

---

## Current Analyses

Implemented analyses include:

- Average age at each disease's first recorded diagnosis
- Length of stay calculations
- Discharge-based 30-day unplanned readmission (primary) and all-cause readmission (secondary)
- Patient-cluster bootstrap confidence intervals for both overall rates
- Diagnosis- and sex-stratified descriptive summaries
- SQL-to-Python data extraction and diagnostic plots

Each eligible discharge contributes one index event. The denominator excludes
discharges without a complete 30-day observation window by 2023-12-31. A return
is linked to the preceding discharge. The primary endpoint counts any unplanned
return within 30 days, even if a planned return happened first; the all-cause
endpoint counts any return. Repeated eligible discharges from the same patient
are retained, with patient-cluster bootstrap intervals to account for
within-patient dependence. These results describe the synthetic scenario and
must not be interpreted as estimates of real-world clinical risk.

Confidence intervals use 2,000 patient-level bootstrap replicates with a fixed
seed so the notebook output is reproducible.

For the current generated dataset:

| Endpoint | Events / eligible discharges | Rate | 95% patient-cluster bootstrap CI |
|---|---:|---:|---:|
| 30-day unplanned | 692 / 3,347 | 20.7% | 19.3%–22.1% |
| 30-day all-cause | 940 / 3,347 | 28.1% | 26.6%–29.5% |

These are reproducible summaries of the seeded synthetic scenario, not
population-level estimates.

Examples of SQL queries include:

```sql
SELECT
    diagnosis,
    AVG(discharge_date - admission_date) AS avg_los
FROM admissions
GROUP BY diagnosis;
```

---

## Planned Analyses

The project is being extended toward more realistic healthcare analytics workflows.

Planned additions include:

- Kaplan-Meier survival analysis
- Cox proportional hazards models
- Machine learning prediction of readmission
- Publication-quality visualisations
- Automated database build pipeline

---

## Running the Project

### Set up Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Create database

```bash
psql -U postgres
CREATE DATABASE healthcare;
```

### Create tables

```bash
psql healthcare -f sql/schema.sql
```

### Generate synthetic data

```bash
python3 src/generate_data.py
```

### Validate generated data

```bash
python3 src/validate_data.py
```

The validator checks required fields, duplicate and orphan records, date and length-of-stay ranges, overlapping admissions, readmission-reason consistency, and complete 30-day follow-up. It exits with a non-zero status when it finds errors. Use `--data-dir` to check CSVs in another directory.

Run the focused endpoint tests with:

```bash
python3 -m unittest discover -s tests -v
```

### Load data

Set a local PostgreSQL connection URL in the environment. The example below is
for a database running locally under the `postgres` user:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:<password>@localhost/healthcare"
```

The loader replaces the contents of the existing tables inside one transaction.

```bash
python3 src/load_data.py
```

### Run analyses

Open:

```text
notebooks/analysis.ipynb
```

and execute the notebook.

---

## Motivation

This repository forms part of a broader programme of upskilling in:

- SQL
- PostgreSQL
- Python
- Health Data Science
- Reproducible Research
- AI-assisted software development

with the aim of developing production-style workflows for healthcare analytics and biostatistics.

## Stretch goals

- Second dataset mirroring claims data
- Combine admissions and claims data through imputation/probabilistic fusion
- swap out python analysis for R (to demonstrate flexibility with workflow)
