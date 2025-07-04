# Dental Appointment Management System 

A web-based Dental Appointment Management System developed using Python, the Flask microframework, MySQL for database management, and HTML/CSS for the frontend. This system allows dental clinics to efficiently manage appointments, including adding, updating, and viewing patient bookings.

## Features

* **Add Appointment:** Register new appointments with patient, dentist, and treatment details.
* **Update Appointment:** Change the status of existing appointments (e.g., Scheduled, Completed, Cancelled).
* **Display All Appointments:** View a table of all upcoming or past appointments.
* **Today's Appointments:** Quickly access appointments scheduled for the current day.

## Technologies Used

* Python
* Flask
* MySQL
* HTML
* CSS
* JavaScript 

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AasthathecoderX/dental-appointment-system
    cd dental-appointment-system
    ```

2.  **Install dependencies:**
    ```bash
    pip install flask
    pip install mysql-connector-python
    ```
    *(Make sure you have Python and pip installed on your system.)*

3.  **Database Setup:**
    * Ensure you have MySQL installed and running.
    * Create a new database for the library management system (e.g., `library`).
    * Update the database connection details in your Flask application configuration file.

4.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    *(Replace `app.py` with the name of your main Flask application file if it's different.)*

5.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000/` (or the address your Flask application is running on).

## Database Schema

```sql
-- Example SQL CREATE TABLE statements
CREATE TABLE patient (
    P_ID INT  PRIMARY KEY,
    Name VARCHAR(100),
    Age INT,
    Contact VARCHAR(20),
    History TEXT
);


CREATE TABLE dentist (
    D_ID INT  PRIMARY KEY,
    Name VARCHAR(100),
    Specialization VARCHAR(100),
    Contact VARCHAR(20),
    Experience INT
);

CREATE TABLE treatment (
    T_ID INT  PRIMARY KEY,
    Name VARCHAR(100),
    Description TEXT,
    Cost DECIMAL(10,2)
);

CREATE TABLE appointment (
    AP_ID INT  PRIMARY KEY,
    P_ID INT,
    D_ID INT,
    T_ID INT,
    Date DATE,
    Status VARCHAR(50),
    Slot VARCHAR(20),
    FOREIGN KEY (P_ID) REFERENCES patient(P_ID) ON DELETE CASCADE,
    FOREIGN KEY (D_ID) REFERENCES dentist(D_ID) ON DELETE CASCADE,
    FOREIGN KEY (T_ID) REFERENCES treatment(T_ID) ON DELETE CASCADE
);

CREATE TABLE payment (
    PM_ID INT  PRIMARY KEY,
    P_ID INT,
    AP_ID INT,
    Amount DECIMAL(10,2),
    Method VARCHAR(50),
    Status VARCHAR(50),
    Date DATE,
    FOREIGN KEY (P_ID) REFERENCES patient(P_ID) ON DELETE CASCADE,
    FOREIGN KEY (AP_ID) REFERENCES appointment(AP_ID) ON DELETE CASCADE
);





 CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin_pass';

 CREATE USER 'frontdesk_user'@'localhost' IDENTIFIED BY 'frontdesk_pass';


-- Give full privileges on dentist table
GRANT SELECT, INSERT, UPDATE, DELETE ON CLINIC.dentist TO 'admin'@'localhost';

-- Give full privileges on patient table
GRANT SELECT, INSERT, UPDATE, DELETE ON CLINIC.patient TO 'admin'@'localhost';

-- Give full privileges on treatment table
GRANT SELECT, INSERT, UPDATE, DELETE ON CLINIC.treatment TO 'admin'@'localhost';

-- Only SELECT privilege on appointment table
GRANT SELECT ON CLINIC.appointment TO 'admin'@'localhost';

-- No privileges on payment table (so, do nothing for payment table)



GRANT SELECT, INSERT, UPDATE, DELETE ON CLINIC.appointment TO 'frontdesk_user'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON CLINIC.payment TO 'frontdesk_user'@'localhost';

FLUSH PRIVILEGES


SHOW GRANTS FOR 'admin'@'localhost';
SHOW GRANTS FOR 'frontdesk_user'@'localhost';

