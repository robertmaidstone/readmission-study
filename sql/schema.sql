DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    patient_id INT PRIMARY KEY,
    age INT,
    sex VARCHAR(10)
);

CREATE TABLE admissions (
    admission_id INT PRIMARY KEY,
    patient_id INT,
    admit_date DATE,
    discharge_date DATE,
    diagnosis VARCHAR(50)
);