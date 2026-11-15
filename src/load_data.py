# src/load_data.py

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://rob:secret123@localhost/healthcare"
)

patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")

patients.to_sql(
    "patients",
    engine,
    if_exists="replace",
    index=False
)

admissions.to_sql(
    "admissions",
    engine,
    if_exists="replace",
    index=False
)