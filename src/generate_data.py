import csv
import random
from datetime import date, timedelta


# Scenario weights are illustrative, not estimates of real-world rates.
READMISSION_REASON_WEIGHTS = {
	"unplanned_related": 15,
	"unplanned_unrelated": 10,
	"planned_follow_up": 10,
	"new_episode": 65,
}


def _next_admission_details(
	previous_diagnosis: str, diagnoses: list[str]
) -> tuple[str, str, int]:
	reason = random.choices(
		population=tuple(READMISSION_REASON_WEIGHTS),
		weights=tuple(READMISSION_REASON_WEIGHTS.values()),
		k=1,
	)[0]

	if reason == "unplanned_related" or reason == "planned_follow_up":
		diagnosis = previous_diagnosis
	elif reason == "unplanned_unrelated":
		diagnosis = random.choice(
			[item for item in diagnoses if item != previous_diagnosis]
		)
	else:
		diagnosis = random.choice(diagnoses)

	if reason == "new_episode":
		gap_days = random.randint(31, 365)
	else:
		gap_days = random.randint(1, 30)

	return reason, diagnosis, gap_days


def generate_data():
	random.seed(42)
	patient_count = 1_000
	min_admissions_per_patient = 1
	max_admissions_per_patient = 10
	start_date = date(2018, 1, 1)
	end_date = date(2024, 12, 31)
	readmission_window_days = 30
	max_length_of_stay_days = 14
	latest_admission_date = end_date - timedelta(
		days=readmission_window_days + max_length_of_stay_days
	)
	min_dob = date(1924, 1, 1)
	max_dob = date(2006, 12, 31)
	diagnoses = [
		"Pneumonia",
		"Heart failure",
		"Type 2 diabetes",
		"Urinary tract infection",
		"Chronic obstructive pulmonary disease",
		"Kidney disease",
		"Sepsis",
		"Stroke",
		"Hip fracture",
		"Chest pain",
	]

	with open("data/patients.csv", "w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(file, fieldnames=["patient_id", "dob", "sex"])
		writer.writeheader()
		for patient_id in range(1, patient_count + 1):
			writer.writerow(
				{
					"patient_id": patient_id,
					"dob": date.fromordinal(
						random.randint(min_dob.toordinal(), max_dob.toordinal())
					).isoformat(),
					"sex": random.choice(["Female", "Male"]),
				}
			)

	admissions = []
	date_range_days = (latest_admission_date - start_date).days
	for patient_id in range(1, patient_count + 1):
		target_admissions = random.randint(
			min_admissions_per_patient, max_admissions_per_patient
		)
		admission_date = start_date + timedelta(
			days=random.randint(0, date_range_days)
		)
		diagnosis = random.choice(diagnoses)
		readmission_reason = "index_admission"
		previous_discharge_date = None

		for admission_number in range(target_admissions):
			if admission_number > 0:
				readmission_reason, diagnosis, gap_days = _next_admission_details(
					previous_diagnosis, diagnoses
				)
				admission_date = previous_discharge_date + timedelta(days=gap_days)
				if admission_date > latest_admission_date:
					break

			max_length_of_stay = min(
				max_length_of_stay_days, (end_date - admission_date).days
			)
			if max_length_of_stay < 1:
				break

			discharge_date = admission_date + timedelta(
				days=random.randint(1, max_length_of_stay)
			)
			admissions.append(
				{
					"patient_id": patient_id,
					"admission_date": admission_date,
					"discharge_date": discharge_date,
					"diagnosis": diagnosis,
					"readmission_reason": readmission_reason,
				}
			)
			previous_discharge_date = discharge_date
			previous_diagnosis = diagnosis

	admissions.sort(
		key=lambda row: (row["admission_date"], row["patient_id"])
	)

	with open("data/admissions.csv", "w", newline="", encoding="utf-8") as file:
		fieldnames = [
			"admission_id",
			"patient_id",
			"admission_date",
			"discharge_date",
			"diagnosis",
			"readmission_reason",
		]
		writer = csv.DictWriter(file, fieldnames=fieldnames)
		writer.writeheader()
		for admission_id, admission in enumerate(admissions, start=1):
			writer.writerow(
				{
					"admission_id": admission_id,
					"patient_id": admission["patient_id"],
					"admission_date": admission["admission_date"].isoformat(),
					"discharge_date": admission["discharge_date"].isoformat(),
					"diagnosis": admission["diagnosis"],
					"readmission_reason": admission["readmission_reason"],
				}
			)


if __name__ == "__main__":
	generate_data()
