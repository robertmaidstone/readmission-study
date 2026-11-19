from datetime import date

import numpy as np
import pandas as pd


UNPLANNED_REASONS = {"unplanned_related", "unplanned_unrelated"}


def build_discharge_outcomes(
    admissions: pd.DataFrame,
    study_end: date,
    readmission_window_days: int = 30,
) -> pd.DataFrame:
    required_columns = {
        "admission_id",
        "patient_id",
        "admission_date",
        "discharge_date",
        "diagnosis",
        "readmission_reason",
        "sex",
    }
    missing_columns = required_columns - set(admissions.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required admission columns: {sorted(missing_columns)}"
        )
    if readmission_window_days < 1:
        raise ValueError("readmission_window_days must be positive")

    ordered = admissions.copy()
    ordered["admission_date"] = pd.to_datetime(
        ordered["admission_date"], errors="raise"
    ).dt.normalize()
    ordered["discharge_date"] = pd.to_datetime(
        ordered["discharge_date"], errors="raise"
    ).dt.normalize()
    ordered = ordered.sort_values(
        ["patient_id", "admission_date", "admission_id"]
    ).reset_index(drop=True)
    by_patient = ordered.groupby("patient_id", sort=False)

    ordered["next_admission_id"] = by_patient["admission_id"].shift(-1)
    ordered["next_admission_date"] = by_patient["admission_date"].shift(-1)
    ordered["next_readmission_reason"] = by_patient["readmission_reason"].shift(-1)
    ordered["days_to_next_admission"] = (
        ordered["next_admission_date"] - ordered["discharge_date"]
    ).dt.days
    next_unplanned_admission_date = pd.Series(
        pd.NaT, index=ordered.index, dtype="datetime64[ns]"
    )
    for _, patient_admissions in ordered.groupby("patient_id", sort=False):
        unplanned_dates = patient_admissions.loc[
            patient_admissions["readmission_reason"].isin(UNPLANNED_REASONS),
            "admission_date",
        ].to_numpy()
        discharge_dates = patient_admissions["discharge_date"].to_numpy()
        positions = np.searchsorted(unplanned_dates, discharge_dates, side="right")
        has_future_unplanned = positions < len(unplanned_dates)
        next_unplanned_admission_date.loc[
            patient_admissions.index[has_future_unplanned]
        ] = pd.to_datetime(unplanned_dates[positions[has_future_unplanned]])
    ordered["next_unplanned_admission_date"] = next_unplanned_admission_date

    follow_up_complete = (
        ordered["discharge_date"]
        + pd.Timedelta(readmission_window_days, unit="D")
        <= pd.Timestamp(study_end)
    )
    within_window = ordered["days_to_next_admission"].between(
        1, readmission_window_days
    )
    ordered = ordered.loc[follow_up_complete].copy()
    within_window = within_window.loc[follow_up_complete]

    ordered["readmission_30d_all_cause"] = within_window.astype(int)
    unplanned_within_window = (
        ordered["next_unplanned_admission_date"] - ordered["discharge_date"]
    ).dt.days.between(1, readmission_window_days)
    ordered["readmission_30d_unplanned"] = unplanned_within_window.astype(int)
    return ordered.rename(
        columns={
            "admission_id": "index_admission_id",
            "admission_date": "index_admission_date",
            "discharge_date": "index_discharge_date",
            "diagnosis": "index_diagnosis",
        }
    ).reset_index(drop=True)

def bootstrap_rate(
    patient_outcomes: pd.DataFrame,
    outcome_column: str,
    bootstrap_replicates: int = 2_000,
    random_seed: int = 42,
) -> dict:
    """
    Cluster bootstrap of a readmission rate at the patient level.

    Parameters
    ----------
    patient_outcomes
        One row per patient containing:
            - eligible_discharges
            - outcome_column
    outcome_column
        Name of event count column.
    bootstrap_replicates
        Number of bootstrap samples.
    random_seed
        RNG seed.

    Returns
    -------
    dict
        events, eligible_discharges, patients,
        rate, ci_lower, ci_upper
    """

    denominators = patient_outcomes["eligible_discharges"].to_numpy()
    numerators = patient_outcomes[outcome_column].to_numpy()

    rng = np.random.default_rng(random_seed)

    sampled_patients = rng.integers(
        0,
        len(patient_outcomes),
        size=(bootstrap_replicates, len(patient_outcomes)),
    )

    sampled_denominators = (
        denominators[sampled_patients]
        .sum(axis=1)
    )

    sampled_numerators = (
        numerators[sampled_patients]
        .sum(axis=1)
    )

    rates = sampled_numerators / sampled_denominators

    lower, upper = np.quantile(
        rates,
        [0.025, 0.975]
    )

    events = int(numerators.sum())
    eligible_discharges = int(denominators.sum())

    return {
        "events": events,
        "eligible_discharges": eligible_discharges,
        "patients": len(patient_outcomes),
        "rate": events / eligible_discharges,
        "ci_lower": lower,
        "ci_upper": upper,
    }

def summarize_readmissions(
    outcomes: pd.DataFrame,
    bootstrap_replicates: int = 2_000,
    random_seed: int = 42,
) -> pd.DataFrame:

    endpoints = {
        "30-day unplanned": "readmission_30d_unplanned",
        "30-day all-cause": "readmission_30d_all_cause",
    }

    required_columns = {
        "patient_id",
        *endpoints.values(),
    }

    missing_columns = (
        required_columns - set(outcomes.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required outcome columns: "
            f"{sorted(missing_columns)}"
        )

    if outcomes.empty:
        raise ValueError(
            "Cannot summarize an empty discharge cohort"
        )

    patient_outcomes = (
        outcomes
        .groupby("patient_id", sort=True)
        .agg(
            eligible_discharges=(
                "patient_id",
                "size",
            ),
            **{
                column: (column, "sum")
                for column in endpoints.values()
            },
        )
    )

    summaries = []

    for endpoint, column in endpoints.items():

        result = bootstrap_rate(
            patient_outcomes=patient_outcomes,
            outcome_column=column,
            bootstrap_replicates=bootstrap_replicates,
            random_seed=random_seed,
        )

        summaries.append(
            {
                "endpoint": endpoint,
                **result,
            }
        )

    return pd.DataFrame(summaries)