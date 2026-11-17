import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


PATIENT_COLUMNS = {"patient_id", "dob", "sex"}
ADMISSION_COLUMNS = {
	"admission_id",
	"patient_id",
	"admission_date",
	"discharge_date",
	"diagnosis",
	"readmission_reason",
}
READMISSION_REASONS = {
	"index_admission",
	"unplanned_related",
	"unplanned_unrelated",
	"planned_follow_up",
	"new_episode",
}
STUDY_START_DATE = date(2019, 1, 1)
STUDY_END_DATE = date(2023, 12, 31)
READMISSION_WINDOW_DAYS = 30
MAX_EXPECTED_LENGTH_OF_STAY_DAYS = 14
MAX_REASONABLE_AGE_YEARS = 120


@dataclass(frozen=True)
class Finding:
	severity: str
	check: str
	details: str


def _row_numbers(mask: pd.Series, limit: int = 10) -> str:
	rows = [str(index + 2) for index in mask[mask].index[:limit]]
	suffix = ", ..." if int(mask.sum()) > limit else ""
	return ", ".join(rows) + suffix


def _add_row_finding(
	findings: list[Finding],
	severity: str,
	check: str,
	filename: str,
	mask: pd.Series,
	details: str,
) -> None:
	mask = mask.fillna(False)
	count = int(mask.sum())
	if count:
		findings.append(
			Finding(
				severity,
				check,
				f"{filename}: {details} ({count} row(s); CSV row(s) "
				f"{_row_numbers(mask)})",
			)
		)


def _read_csv(path: Path, findings: list[Finding]) -> pd.DataFrame | None:
	if not path.is_file():
		findings.append(Finding("ERROR", "file_exists", f"Missing file: {path}"))
		return None

	try:
		frame = pd.read_csv(path, dtype="string")
	except pd.errors.EmptyDataError:
		findings.append(Finding("ERROR", "read_csv", f"File is empty: {path}"))
		return None
	except pd.errors.ParserError as error:
		findings.append(
			Finding("ERROR", "read_csv", f"Could not parse {path}: {error}")
		)
		return None

	for column in frame.select_dtypes(include="string").columns:
		frame[column] = frame[column].str.strip()
	return frame


def _check_columns(
	frame: pd.DataFrame,
	required_columns: set[str],
	filename: str,
	findings: list[Finding],
) -> bool:
	missing = sorted(required_columns - set(frame.columns))
	for column in missing:
		findings.append(
			Finding("ERROR", "required_columns", f"{filename} is missing column {column!r}")
		)
	return not missing


def _check_missing_values(
	frame: pd.DataFrame,
	required_columns: set[str],
	filename: str,
	findings: list[Finding],
) -> None:
	for column in sorted(required_columns):
		missing = frame[column].isna() | frame[column].eq("").fillna(False)
		_add_row_finding(
			findings,
			"ERROR",
			"missing_values",
			filename,
			missing,
			f"{column} is missing",
		)


def _parse_dates(
	frame: pd.DataFrame,
	column: str,
	filename: str,
	findings: list[Finding],
) -> pd.Series:
	raw = frame[column]
	parsed = pd.to_datetime(raw, errors="coerce")
	invalid = raw.notna() & raw.ne("") & parsed.isna()
	_add_row_finding(
		findings,
		"ERROR",
		"invalid_dates",
		filename,
		invalid,
		f"{column} is not a valid date",
	)
	return parsed


def _check_ids(
	frame: pd.DataFrame,
	column: str,
	filename: str,
	findings: list[Finding],
) -> pd.Series:
	raw = frame[column]
	numeric = pd.to_numeric(raw, errors="coerce")
	missing = raw.isna() | raw.eq("").fillna(False)
	invalid = ~missing & (numeric.isna() | numeric.mod(1).ne(0))
	_add_row_finding(
		findings,
		"ERROR",
		"invalid_ids",
		filename,
		invalid,
		f"{column} must be a whole number",
	)
	nonpositive = numeric.notna() & numeric.le(0)
	_add_row_finding(
		findings,
		"ERROR",
		"invalid_ids",
		filename,
		nonpositive,
		f"{column} must be positive",
	)
	return numeric


def _check_duplicate_ids(
	ids: pd.Series,
	column: str,
	filename: str,
	findings: list[Finding],
) -> None:
	duplicates = ids.notna() & ids.duplicated(keep=False)
	_add_row_finding(
		findings,
		"ERROR",
		"duplicate_ids",
		filename,
		duplicates,
		f"{column} is duplicated",
	)


def _check_overlaps_and_reasons(
	admissions: pd.DataFrame,
	admission_ids: pd.Series,
	patient_ids: pd.Series,
	admission_dates: pd.Series,
	discharge_dates: pd.Series,
	findings: list[Finding],
) -> None:
	valid_stays = (
		patient_ids.notna()
		& admission_dates.notna()
		& discharge_dates.notna()
		& discharge_dates.gt(admission_dates)
	)
	ordered = pd.DataFrame(
		{
			"patient_id": patient_ids[valid_stays],
			"admission_id": admission_ids[valid_stays],
			"admission_date": admission_dates[valid_stays],
			"discharge_date": discharge_dates[valid_stays],
			"diagnosis": admissions.loc[valid_stays, "diagnosis"],
			"readmission_reason": admissions.loc[valid_stays, "readmission_reason"],
			"csv_row": admissions.index[valid_stays] + 2,
		}
	).sort_values(["patient_id", "admission_date", "admission_id"])

	for patient_id, events in ordered.groupby("patient_id", sort=False):
		rows = list(events.to_dict("records"))
		if not rows:
			continue

		if (
			pd.notna(rows[0]["readmission_reason"])
			and rows[0]["readmission_reason"] != "index_admission"
		):
			findings.append(
				Finding(
					"ERROR",
					"readmission_reason",
					f"patient_id {patient_id}: first admission must be "
					"'index_admission' (CSV row {rows[0]['csv_row']})",
				)
			)

		max_discharge = None
		max_discharge_id = None
		for row in rows:
			if (
				max_discharge is not None
				and row["admission_date"] <= max_discharge
			):
				findings.append(
					Finding(
						"ERROR",
						"overlapping_stays",
						f"patient_id {patient_id}: admission_id "
						f"{row['admission_id']} overlaps admission_id "
						f"{max_discharge_id} (CSV row {row['csv_row']})",
					)
				)
			if max_discharge is None or row["discharge_date"] > max_discharge:
				max_discharge = row["discharge_date"]
				max_discharge_id = row["admission_id"]

		for previous, current in zip(rows, rows[1:]):
			reason = current["readmission_reason"]
			if pd.isna(reason) or reason == "":
				continue
			if reason not in READMISSION_REASONS:
				continue
			if reason == "index_admission":
				findings.append(
					Finding(
						"ERROR",
						"readmission_reason",
						f"patient_id {patient_id}: only the first admission may "
						f"be 'index_admission' (CSV row {current['csv_row']})",
					)
				)
				continue

			gap_days = (
				current["admission_date"] - previous["discharge_date"]
			).days
			if reason in {"unplanned_related", "unplanned_unrelated", "planned_follow_up"}:
				if not 1 <= gap_days <= READMISSION_WINDOW_DAYS:
					findings.append(
						Finding(
							"ERROR",
							"readmission_reason",
							f"patient_id {patient_id}: {reason!r} requires a "
							f"1–{READMISSION_WINDOW_DAYS}-day gap; found "
							f"{gap_days} days (CSV row {current['csv_row']})",
						)
					)
			elif reason == "new_episode" and not 31 <= gap_days <= 365:
				findings.append(
					Finding(
						"ERROR",
						"readmission_reason",
						f"patient_id {patient_id}: 'new_episode' requires a "
						f"31–365-day gap; found {gap_days} days "
						f"(CSV row {current['csv_row']})",
					)
				)

			has_both_diagnoses = pd.notna(previous["diagnosis"]) and pd.notna(
				current["diagnosis"]
			)
			if has_both_diagnoses and (
				reason in {"unplanned_related", "planned_follow_up"}
				and current["diagnosis"] != previous["diagnosis"]
			):
				findings.append(
					Finding(
						"ERROR",
						"readmission_reason",
						f"patient_id {patient_id}: {reason!r} should retain the "
						f"previous diagnosis (CSV row {current['csv_row']})",
					)
				)
			elif has_both_diagnoses and (
				reason == "unplanned_unrelated"
				and current["diagnosis"] == previous["diagnosis"]
			):
				findings.append(
					Finding(
						"ERROR",
						"readmission_reason",
						f"patient_id {patient_id}: 'unplanned_unrelated' should "
						f"change diagnosis (CSV row {current['csv_row']})",
					)
				)


def validate_data(data_dir: Path) -> list[Finding]:
	findings: list[Finding] = []
	patients = _read_csv(data_dir / "patients.csv", findings)
	admissions = _read_csv(data_dir / "admissions.csv", findings)
	if patients is None or admissions is None:
		return findings

	patient_columns_ok = _check_columns(
		patients, PATIENT_COLUMNS, "patients.csv", findings
	)
	admission_columns_ok = _check_columns(
		admissions, ADMISSION_COLUMNS, "admissions.csv", findings
	)
	if not patient_columns_ok or not admission_columns_ok:
		return findings
	if patients.empty:
		findings.append(Finding("ERROR", "empty_table", "patients.csv contains no records"))
	if admissions.empty:
		findings.append(Finding("ERROR", "empty_table", "admissions.csv contains no records"))

	_check_missing_values(patients, PATIENT_COLUMNS, "patients.csv", findings)
	_check_missing_values(admissions, ADMISSION_COLUMNS, "admissions.csv", findings)

	patient_ids = _check_ids(patients, "patient_id", "patients.csv", findings)
	admission_ids = _check_ids(admissions, "admission_id", "admissions.csv", findings)
	admission_patient_ids = _check_ids(
		admissions, "patient_id", "admissions.csv", findings
	)
	_check_duplicate_ids(patient_ids, "patient_id", "patients.csv", findings)
	_check_duplicate_ids(admission_ids, "admission_id", "admissions.csv", findings)

	exact_duplicates = patients.duplicated(keep=False)
	_add_row_finding(
		findings,
		"ERROR",
		"duplicate_rows",
		"patients.csv",
		exact_duplicates,
		"exact duplicate patient row",
	)
	exact_duplicates = admissions.duplicated(keep=False)
	_add_row_finding(
		findings,
		"ERROR",
		"duplicate_rows",
		"admissions.csv",
		exact_duplicates,
		"exact duplicate admission row",
	)

	admission_dates = _parse_dates(
		admissions, "admission_date", "admissions.csv", findings
	)
	discharge_dates = _parse_dates(
		admissions, "discharge_date", "admissions.csv", findings
	)
	dobs = _parse_dates(patients, "dob", "patients.csv", findings)

	patient_keys = set(patient_ids.dropna())
	orphan_patients = admission_patient_ids.notna() & ~admission_patient_ids.isin(
		patient_keys
	)
	_add_row_finding(
		findings,
		"ERROR",
		"orphan_admissions",
		"admissions.csv",
		orphan_patients,
		"patient_id does not exist in patients.csv",
	)

	invalid_stays = (
		admission_dates.notna()
		& discharge_dates.notna()
		& discharge_dates.le(admission_dates)
	)
	_add_row_finding(
		findings,
		"ERROR",
		"invalid_stay_dates",
		"admissions.csv",
		invalid_stays,
		"discharge_date must be after admission_date",
	)

	length_of_stay = (discharge_dates - admission_dates).dt.days
	long_stays = length_of_stay.gt(MAX_EXPECTED_LENGTH_OF_STAY_DAYS) & length_of_stay.le(365)
	_add_row_finding(
		findings,
		"WARNING",
		"long_stays",
		"admissions.csv",
		long_stays,
		f"length of stay exceeds the generator's "
		f"{MAX_EXPECTED_LENGTH_OF_STAY_DAYS}-day range",
	)
	extreme_stays = length_of_stay.gt(365)
	_add_row_finding(
		findings,
		"ERROR",
		"extreme_stays",
		"admissions.csv",
		extreme_stays,
		"length of stay exceeds one year",
	)

	study_start = pd.Timestamp(STUDY_START_DATE)
	study_end = pd.Timestamp(STUDY_END_DATE)
	outside_study = admission_dates.notna() & (
		admission_dates.lt(study_start) | admission_dates.gt(study_end)
	)
	_add_row_finding(
		findings,
		"WARNING",
		"study_date_range",
		"admissions.csv",
		outside_study,
		f"admission_date is outside {STUDY_START_DATE}–{STUDY_END_DATE}",
	)

	dob_by_patient = pd.DataFrame(
		{"patient_id": patient_ids, "dob": dobs}
	).dropna(subset=["patient_id", "dob"])
	dob_by_patient = dob_by_patient.drop_duplicates("patient_id", keep="first")
	admission_dobs = admission_patient_ids.map(
		dob_by_patient.set_index("patient_id")["dob"]
	)
	age_days = (admission_dates - admission_dobs).dt.days
	unreasonable_age = age_days.lt(0) | age_days.gt(MAX_REASONABLE_AGE_YEARS * 365.25)
	_add_row_finding(
		findings,
		"ERROR",
		"unreasonable_age",
		"admissions.csv",
		unreasonable_age,
		f"age at admission must be between 0 and {MAX_REASONABLE_AGE_YEARS} years",
	)

	unknown_sex = (
		patients["sex"].notna()
		& patients["sex"].ne("")
		& ~patients["sex"].str.casefold().isin({"female", "male"})
	)
	_add_row_finding(
		findings,
		"WARNING",
		"unexpected_sex",
		"patients.csv",
		unknown_sex,
		"sex is outside the generator's Female/Male categories",
	)

	invalid_reasons = (
		admissions["readmission_reason"].notna()
		& admissions["readmission_reason"].ne("")
		& ~admissions["readmission_reason"].isin(READMISSION_REASONS)
	)
	_add_row_finding(
		findings,
		"ERROR",
		"invalid_readmission_reason",
		"admissions.csv",
		invalid_reasons,
		"readmission_reason is not a recognized category",
	)

	insufficient_follow_up = discharge_dates.notna() & discharge_dates.gt(
		study_end - pd.Timedelta(days=READMISSION_WINDOW_DAYS)
	)
	_add_row_finding(
		findings,
		"WARNING",
		"incomplete_follow_up",
		"admissions.csv",
		insufficient_follow_up,
		f"discharge has less than {READMISSION_WINDOW_DAYS} days of "
		"observation before the study end date",
	)

	if not admission_dates.dropna().is_monotonic_increasing:
		findings.append(
			Finding(
				"WARNING",
				"chronological_order",
				"admissions.csv rows are not globally ordered by admission_date",
			)
		)

	natural_key = ["patient_id", "admission_date", "discharge_date", "diagnosis"]
	complete_natural_key = admissions[natural_key].notna().all(axis=1)
	for column in natural_key:
		complete_natural_key &= admissions[column].ne("").fillna(False)
	duplicate_admission_key = complete_natural_key & admissions.duplicated(
		natural_key,
		keep=False,
	)
	_add_row_finding(
		findings,
		"ERROR",
		"duplicate_admissions",
		"admissions.csv",
		duplicate_admission_key,
		"patient, admission date, discharge date, and diagnosis are duplicated",
	)

	_check_overlaps_and_reasons(
		admissions,
		admission_ids,
		admission_patient_ids,
		admission_dates,
		discharge_dates,
		findings,
	)
	return findings


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Check the generated patient and admission CSV files."
	)
	parser.add_argument(
		"--data-dir",
		type=Path,
		default=Path(__file__).resolve().parents[1] / "data",
		help="Directory containing patients.csv and admissions.csv",
	)
	args = parser.parse_args()

	findings = validate_data(args.data_dir.expanduser().resolve())
	errors = sum(finding.severity == "ERROR" for finding in findings)
	warnings = sum(finding.severity == "WARNING" for finding in findings)
	print(f"Data quality check: {errors} error(s), {warnings} warning(s)")
	for finding in findings:
		print(f"[{finding.severity}] {finding.check}: {finding.details}")
	if not findings:
		print("No issues found.")
	return 1 if errors else 0


if __name__ == "__main__":
	raise SystemExit(main())
