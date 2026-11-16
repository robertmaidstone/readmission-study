# Synthetic Healthcare Readmission Study

![Python](https://img.shields.io/badge/Python-3.14+-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)
![Last Commit](https://img.shields.io/github/last-commit/robertmaidstone/readmission-study?cacheSeconds=60)

## Overview

This repository contains a synthetic healthcare analytics workflow developed to learn and demonstrate modern health data science practices using PostgreSQL, SQL, Python and Jupyter notebooks.

Synthetic patient and hospital admission records are generated programmatically, loaded into a PostgreSQL database and analysed using SQL and Python. The project is designed to mirror common healthcare analytics workflows used in NHS, academic and industry settings.

The primary objectives are:

- Building relational healthcare databases
- Cohort extraction using SQL
- Integrating PostgreSQL and Python
- Reproducible health data science workflows
- Exploratory analysis of admissions data
- Survival and readmission analyses

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

notebooks/
    analysis.ipynb

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
| admit_date | Admission date |
| discharge_date | Discharge date |
| diagnosis | Primary diagnosis |

Future versions will incorporate:

- Multiple admissions per patient
- Readmission events
- Comorbidity burden
- Medication records
- Mortality outcomes

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

- Patient demographics
- Average age by diagnosis
- Length of stay calculations
- Admission frequency analyses
- SQL-to-Python data extraction

Examples of SQL queries include:

```sql
SELECT
    diagnosis,
    AVG(discharge_date - admit_date) AS avg_los
FROM admissions
GROUP BY diagnosis;
```

---

## Planned Analyses

The project is being extended toward more realistic healthcare analytics workflows.

Planned additions include:

- Readmission rate estimation
- Kaplan-Meier survival analysis
- Cox proportional hazards models
- Machine learning prediction of readmission
- Publication-quality visualisations
- Automated database build pipeline

---

## Running the Project

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

### Load data

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
