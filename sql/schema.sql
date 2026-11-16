DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    patient_id INT PRIMARY KEY,
    dob DATE,
    sex VARCHAR(10)
);

CREATE TABLE admissions (
    admission_id INT PRIMARY KEY,
    patient_id INT,
    admission_date DATE,
    discharge_date DATE,
    diagnosis VARCHAR(50),
    readmission_reason VARCHAR(30) NOT NULL
        CHECK (
            readmission_reason IN (
                'index_admission',
                'unplanned_related',
                'unplanned_unrelated',
                'planned_follow_up',
                'new_episode'
            )
        ),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CHECK (discharge_date > admission_date)
);