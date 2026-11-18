import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from db_config import DATABASE_URL


def load_data(data_dir: Path) -> None:
    engine = create_engine(DATABASE_URL)
    patients = pd.read_csv(data_dir / "patients.csv", parse_dates=["dob"])
    admissions = pd.read_csv(
        data_dir / "admissions.csv",
        parse_dates=["admission_date", "discharge_date"],
    )

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM admissions"))
        connection.execute(text("DELETE FROM patients"))
        patients.to_sql(
            "patients",
            connection,
            if_exists="append",
            index=False,
        )
        admissions.to_sql(
            "admissions",
            connection,
            if_exists="append",
            index=False,
        )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Load the synthetic CSV files into PostgreSQL."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=project_root / "data",
        help="Directory containing patients.csv and admissions.csv",
    )
    args = parser.parse_args()
    load_data(args.data_dir.expanduser().resolve())
    print("Loaded patients.csv and admissions.csv into PostgreSQL.")


if __name__ == "__main__":
    main()