import unittest
from datetime import date

import pandas as pd

from src.readmission_analysis import (
    build_discharge_outcomes,
    summarize_readmissions,
)


def make_admissions(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "admission_id",
            "patient_id",
            "admission_date",
            "discharge_date",
            "diagnosis",
            "readmission_reason",
            "sex",
        ],
    )


class BuildDischargeOutcomesTests(unittest.TestCase):
    def test_outcome_is_anchored_on_every_eligible_discharge(self) -> None:
        admissions = make_admissions(
            [
                (1, 1, "2023-01-01", "2023-01-02", "A", "index_admission", "Female"),
                (2, 1, "2023-01-03", "2023-01-04", "A", "unplanned_related", "Female"),
                (3, 1, "2023-01-10", "2023-01-11", "A", "planned_follow_up", "Female"),
                (
                    4,
                    1,
                    "2023-01-20",
                    "2023-01-21",
                    "B",
                    "unplanned_unrelated",
                    "Female",
                ),
                (5, 1, "2023-02-21", "2023-02-22", "B", "new_episode", "Female"),
                (6, 2, "2023-01-01", "2023-01-02", "A", "index_admission", "Male"),
                (7, 2, "2023-02-01", "2023-02-02", "A", "planned_follow_up", "Male"),
                (8, 3, "2023-01-01", "2023-01-02", "A", "index_admission", "Female"),
                (9, 3, "2023-02-02", "2023-02-03", "A", "new_episode", "Female"),
            ]
        )

        outcomes = build_discharge_outcomes(admissions, date(2023, 12, 31))

        self.assertEqual(len(outcomes), 9)
        self.assertEqual(
            outcomes["readmission_30d_all_cause"].tolist(),
            [1, 1, 1, 0, 0, 1, 0, 0, 0],
        )
        self.assertEqual(
            outcomes["readmission_30d_unplanned"].tolist(),
            [1, 1, 1, 0, 0, 0, 0, 0, 0],
        )
        self.assertEqual(
            outcomes["days_to_next_admission"].iloc[[0, 5, 7]].tolist(),
            [1, 30, 31],
        )

    def test_requires_complete_follow_up_through_day_30(self) -> None:
        admissions = make_admissions(
            [
                (1, 1, "2023-11-29", "2023-12-01", "A", "index_admission", "Female"),
                (2, 2, "2023-11-30", "2023-12-02", "A", "index_admission", "Male"),
            ]
        )

        outcomes = build_discharge_outcomes(admissions, date(2023, 12, 31))

        self.assertEqual(outcomes["index_admission_id"].tolist(), [1])
        self.assertEqual(
            outcomes["index_discharge_date"].iloc[0],
            pd.Timestamp("2023-12-01"),
        )


class SummarizeReadmissionsTests(unittest.TestCase):
    def test_cluster_bootstrap_reports_counts_rates_and_repeatable_intervals(
        self,
    ) -> None:
        admissions = make_admissions(
            [
                (1, 1, "2023-01-01", "2023-01-02", "A", "index_admission", "Female"),
                (2, 1, "2023-01-03", "2023-01-04", "A", "unplanned_related", "Female"),
                (3, 1, "2023-01-05", "2023-01-06", "A", "planned_follow_up", "Female"),
                (4, 2, "2023-01-01", "2023-01-02", "B", "index_admission", "Male"),
            ]
        )
        outcomes = build_discharge_outcomes(admissions, date(2023, 12, 31))

        first = summarize_readmissions(
            outcomes, bootstrap_replicates=200, random_seed=7
        )
        second = summarize_readmissions(
            outcomes, bootstrap_replicates=200, random_seed=7
        )

        unplanned, all_cause = first.to_dict("records")
        self.assertEqual(
            (unplanned["events"], unplanned["eligible_discharges"]),
            (1, 4),
        )
        self.assertEqual(
            (all_cause["events"], all_cause["eligible_discharges"]),
            (2, 4),
        )
        self.assertGreaterEqual(all_cause["events"], unplanned["events"])
        self.assertEqual(
            first[["ci_lower", "ci_upper"]].values.tolist(),
            second[["ci_lower", "ci_upper"]].values.tolist(),
        )
        self.assertLessEqual(unplanned["ci_lower"], unplanned["rate"])
        self.assertGreaterEqual(unplanned["ci_upper"], unplanned["rate"])

    def test_rejects_empty_cohort(self) -> None:
        empty = pd.DataFrame(
            columns=[
                "patient_id",
                "readmission_30d_unplanned",
                "readmission_30d_all_cause",
            ]
        )
        with self.assertRaisesRegex(ValueError, "empty discharge cohort"):
            summarize_readmissions(empty)


if __name__ == "__main__":
    unittest.main()
