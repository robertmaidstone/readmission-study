import csv
import random
from datetime import date, timedelta


def generate_data():
	random.seed(42)
	patient_count = 1_000
	min_admissions_per_patient = 1
	max_admissions_per_patient = 10
	start_date = date(2018, 1, 1)
	end_date = date(2024, 12, 31)
	date_range_days = (end_date - start_date).days
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

	with open("patients.csv", "w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(file, fieldnames=["patient_id", "age", "sex"])
		writer.writeheader()
		for patient_id in range(1, patient_count + 1):
			writer.writerow(
				{
					"patient_id": patient_id,
					"age": random.randint(18, 100),
					"sex": random.choice(["Female", "Male"]),
				}
			)

	with open("admissions.csv", "w", newline="", encoding="utf-8") as file:
		writer = csv.DictWriter(
			file,
			fieldnames=[
				"admission_id",
				"patient_id",
				"admission_date",
				"discharge_date",
				"diagnosis",
			],
		)
		writer.writeheader()
		admission_id = 1
		for patient_id in range(1, patient_count + 1):
			for _ in range(
				random.randint(min_admissions_per_patient, max_admissions_per_patient)
			):
				admission_date = start_date + timedelta(
					days=random.randint(0, date_range_days)
				)
				discharge_date = admission_date + timedelta(days=random.randint(1, 14))
				writer.writerow(
					{
						"admission_id": admission_id,
						"patient_id": patient_id,
						"admission_date": admission_date.isoformat(),
						"discharge_date": discharge_date.isoformat(),
						"diagnosis": random.choice(diagnoses),
					}
				)
				admission_id += 1


if __name__ == "__main__":
	generate_data()
