from flask import Flask, render_template, request,flash,redirect,url_for,jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import datetime
import logging
import logging.handlers as handlers
from logging.handlers import RotatingFileHandler
import mysql.connector
import os
import platform
from flask import session
from textblob import TextBlob
import re
import logging

import secrets

global db_uname
global db_upass
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)




def clean_text(text):
    """Use AI to spell-check and correct text."""
    blob = TextBlob(text)
    return str(blob.correct())

def validate_appointment_data(data):
    """Validate the appointment data with AI + pattern checking."""
    errors = []
    cleaned_data = data.copy()

    # Validate IDs
    id_fields = ['appointment_id', 'patient_id', 'dentist_id', 'treatment_id']
    for field in id_fields:
        value = data.get(field, '')
        if not re.match(r'^[A-Za-z0-9]+$', value):
            errors.append(f"Invalid {field}: Only letters and numbers allowed.")

    # Clean the status field
    if 'status' in data:
        cleaned_data['status'] = clean_text(data['status'])

    return errors, cleaned_data







def db_connect():
    # Use username and password from session
    user = session.get('db_username')
    password = session.get('db_password')

    if not user or not password:
        raise ValueError("No user credentials found in session.")

    return mysql.connector.connect(
        host="localhost",
        user=user,
        password=password,
        database="CLINIC"
    )

  

    


#Functions for appointment

def add_appointment_db(data):
    try:
        conn = db_connect()
        cursor = conn.cursor()

        # Validate the data before inserting
        errors, cleaned_data = validate_appointment_data(data)
        if errors:
            for err in errors:
                flash(err, 'error')
            return False  # Stop insertion if there are errors

        sql = """
            INSERT INTO appointment (AP_ID, P_ID, D_ID, T_ID, Date, Status, Slot)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        val = (
            cleaned_data['appointment_id'],
            cleaned_data['patient_id'],
            cleaned_data['dentist_id'],
            cleaned_data['treatment_id'],
            cleaned_data['date'],
            cleaned_data['status'],
            cleaned_data['slot']
        )

        cursor.execute(sql, val)
        conn.commit()
        print(cursor.rowcount, "appointment inserted.")
        flash("Appointment successfully added.", "success")
        return True

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        flash("Database error occurred.", "error")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Connection closed.")
            
            


def update_appoint_db():
    appointment_id = request.form['appointment_id']
    new_status = request.form['status']

    try:
        conn = db_connect()
        cursor = conn.cursor()

        # Validate appointment_id pattern
        if not re.match(r'^[A-Za-z0-9]+$', appointment_id):
            flash("Invalid Appointment ID: Only letters and numbers allowed.", "error")
            return redirect(url_for('appointment'))

        # Clean (spell-check) status field
        cleaned_status = clean_text(new_status)

        sql = "UPDATE appointment SET Status = %s WHERE AP_ID = %s"
        val = (cleaned_status, appointment_id)

        cursor.execute(sql, val)
        conn.commit()

        if cursor.rowcount == 0:
            flash("No appointment found with that ID.", "error")
        else:
            flash("Appointment updated successfully!", "success")
            logging.info(f"Appointment {appointment_id} updated to status {cleaned_status}")

    except mysql.connector.Error as e:
        logging.error(f"Error updating appointment: {e}")
        flash("Failed to update appointment.", "error")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Connection closed.")

    return redirect(url_for('appointment'))




def all_appoint_db():
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    try:
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM appointment"
        cursor.execute(sql)
        result = cursor.fetchall()

    except mysql.connector.Error as err:
        logging.error(f"Error fetching appointments: {err}")
        html += "<p style='color: red; text-align: center;'>Error loading appointments. Please try again later.</p>"

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    # Generate HTML table
    if result:
        html += """
            <table style='border-collapse: collapse; width: 70%; margin: 0 auto;'>
                <tr style='background-color: #333; color: white;'>
                    <th style='padding: 10px;'>AP_ID</th>
                    <th style='padding: 10px;'>P_ID</th>
                    <th style='padding: 10px;'>D_ID</th>
                    <th style='padding: 10px;'>T_ID</th>
                    <th style='padding: 10px;'>Date</th>
                    <th style='padding: 10px;'>Status</th>
                    <th style='padding: 10px;'>Slot</th>
                </tr>
        """

        for row in result:
            # Clean the Status (just to be extra sure no typos appear)
            cleaned_status = clean_text(row['Status'])

            html += "<tr style='background-color: #f9f9f9;'>\n"
            html += f"<td style='padding: 10px;'>{row['AP_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['P_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['D_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['T_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Date']}</td>\n"
            html += f"<td style='padding: 10px;'>{cleaned_status}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Slot']}</td>\n"
            html += "</tr>\n"

        html += "</table>"
    else:
        html += "<p style='text-align: center; font-size: 18px;'>No appointments found.</p>"

    return html


   
def today_appoint_db(data):
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    if 't_date' in data and data['t_date']:
        try:
            conn = db_connect()
            cursor = conn.cursor(dictionary=True)

            sql = "SELECT * FROM appointment WHERE `Date` = %s"
            val = (data['t_date'],)
            cursor.execute(sql, val)
            result = cursor.fetchall()

        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
            html += "<p style='color: red; text-align: center;'>Error retrieving today's appointments. Please try again later.</p>"
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    # Generate HTML table
    html += """
        <table style='border-collapse: collapse; width: 70%; margin: 0 auto;'>
            <tr style='background-color: #333; color: white;'>
                <th style='padding: 10px;'>AP_ID</th>
                <th style='padding: 10px;'>P_ID</th>
                <th style='padding: 10px;'>D_ID</th>
                <th style='padding: 10px;'>T_ID</th>
                <th style='padding: 10px;'>Date</th>
                <th style='padding: 10px;'>Status</th>
                <th style='padding: 10px;'>Slot</th>
            </tr>
    """

    if result:
        for row in result:
            # Clean the status to correct any spelling mistakes
            cleaned_status = clean_text(row['Status'])

            # Change row color based on status
            if cleaned_status.lower() == 'cancelled':
                row_style = "background-color: #ffcccc;"  # Light red
            elif cleaned_status.lower() == 'completed':
                row_style = "background-color: #ccffcc;"  # Light green
            else:
                row_style = "background-color: #f9f9f9;"  # Normal

            html += f"<tr style='{row_style}'>\n"
            html += f"<td style='padding: 10px;'>{row['AP_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['P_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['D_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['T_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Date']}</td>\n"
            html += f"<td style='padding: 10px;'>{cleaned_status}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Slot']}</td>\n"
            html += "</tr>\n"

        html += "</table>"
    else:
        html += "<p style='text-align: center; font-size: 18px;'>No appointments found for today.</p>"

    return html


#Functions for patients


def validate_patient_data(data):
    """Validate and clean patient data."""
    errors = []
    cleaned_data = {}

    # Validate and clean patient ID
    pid = data.get('pid', '').strip()
    if not re.match(r'^[A-Za-z0-9]+$', pid):
        errors.append("Invalid Patient ID: Only letters and numbers allowed.")
    cleaned_data['pid'] = pid

    # Validate and clean name (spell check)
    name = data.get('name', '').strip()
    if name:
        cleaned_data['name'] = clean_text(name)
    else:
        errors.append("Name cannot be empty.")

    # Validate age
    age = data.get('age', '').strip()
    if not age.isdigit() or int(age) <= 0:
        errors.append("Invalid Age: Must be a positive number.")
    cleaned_data['age'] = int(age) if age.isdigit() else None

    # Validate contact number (basic pattern)
    contact = data.get('contact', '').strip()
    if not re.match(r'^\d{10}$', contact):
        errors.append("Invalid Contact Number: Please enter a 10-digit phone number.")  # More specific message
    cleaned_data['contact'] = contact

    # Clean history (spell check)
    history = data.get('history', '').strip()
    cleaned_data['history'] = clean_text(history) if history else ''

    return errors, cleaned_data


def add_patient_db(data):
    try:
        conn = db_connect()
        cursor = conn.cursor()

        # Validate data
        errors, cleaned_data = validate_patient_data(data)
        if errors:
            for err in errors:
                flash(err, 'error')
            return False  # Don't insert if there are validation errors

        sql = """
            INSERT INTO patient (`P_ID`, `Name`, `Age`, `Contact`, `History`)
            VALUES (%s, %s, %s, %s, %s)
        """
        val = (
            cleaned_data['pid'],
            cleaned_data['name'],
            cleaned_data['age'],
            cleaned_data['contact'],
            cleaned_data['history'],
        )

        cursor.execute(sql, val)
        conn.commit()
        flash("Patient added successfully!", "success")
        print(cursor.rowcount, "patient inserted.")
        return True

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        flash("Database error occurred while adding patient.", "error")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Connection closed.")
            
            
    

def delete_patient_db(patient_id):
    # Validate patient_id (optional: allows only alphanumeric)
    if not re.match(r'^[A-Za-z0-9]+$', patient_id):
        flash("Invalid Patient ID format. Only letters and numbers allowed.", "error")
        return False

    try:
        conn = db_connect()
        cursor = conn.cursor()

        sql = "DELETE FROM patient WHERE `P_ID` = %s"
        val = (patient_id,)

        cursor.execute(sql, val)
        conn.commit()

        if cursor.rowcount > 0:
            flash(f"Patient {patient_id} deleted successfully.", "success")
            print(cursor.rowcount, "record deleted.")
            return True
        else:
            flash(f"No patient found with ID {patient_id}.", "warning")
            return False

    except mysql.connector.Error as err:
        logging.error(f"Error deleting patient {patient_id}: {err}")
        flash("Database error occurred while deleting patient.", "error")
        return False

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            logging.info("Database connection closed.")
            
            
    
    
    
def display_patient_db():
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    try:
        
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM patient"
        cursor.execute(sql)
        result = cursor.fetchall()
        
    except mysql.connector.Error as err:
        logging.error(f"Error fetching patients details: {err}")
        html += "<p>Error loading patients details.</p>"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    # Generate HTML table (same as before)
    html = "<div style='margin-bottom: 100px;'></div>"
    html += "<table style='border-collapse: collapse; width: 70%;'>\n" 
    html += "<tr style='background-color: #333; color: white;'>\n" 
    html += "<th style='padding: 10px;'>P_ID</th>\n"
    html += "<th style='padding: 10px;'>Name</th>\n" 
    html += "<th style='padding: 10px;'>Age</th>\n" 
    html += "<th style='padding: 10px;'>Contact</th>\n"
    html += "<th style='padding: 10px;'>History</th>\n"
    html += "</tr>\n" 

    if result:
        for row in result:
            html += "<tr style='background-color: #f2f2f2;'>\n"
            html += "<td style='padding: 10px;'>{}</td>\n".format(row['P_ID'])
            html += "<td style='padding: 10px;'>{}</td>\n".format(row['Name'])
            html += "<td style='padding: 10px;'>{}</td>\n".format(row['Age'])
            html += "<td style='padding: 10px;'>{}</td>\n".format(row['Contact'])
            html += "<td style='padding: 10px;'>{}</td>\n".format(row['History'])
            html += "</tr>\n"
        html += "</table>"
    else:
        html += "<p>No patient records found.</p>"

    return html


def validate_dentist_data(data):
    """Validate and clean dentist data."""
    errors = []
    cleaned_data = {}

    dentist_id = data.get('dentist_id', '').strip()
    if not re.match(r'^[A-Za-z0-9]+$', dentist_id):
        errors.append("Invalid Dentist ID: Only letters and numbers allowed.")
    cleaned_data['dentist_id'] = dentist_id

    name = data.get('name', '').strip()
    if name:
        cleaned_data['name'] = clean_text(name)
    else:
        errors.append("Name cannot be empty.")

    specialization = data.get('specialization', '').strip()
    if specialization:
        cleaned_data['specialization'] = clean_text(specialization)
    else:
        errors.append("Specialization cannot be empty.")

    contact = data.get('contact', '').strip()
    if not re.match(r'^\d{10}$', contact):
        errors.append("Invalid Contact: Must be a 10-digit number.")
    cleaned_data['contact'] = contact

    experience = data.get('experience', '').strip()
    if not experience.isdigit() or int(experience) < 0:
        errors.append("Invalid Experience: Must be a non-negative number.")
    cleaned_data['experience'] = int(experience) if experience.isdigit() else None

    return errors, cleaned_data

def add_dentist_db(data):
    try:
        conn = db_connect()
        cursor = conn.cursor()
        errors, cleaned_data = validate_dentist_data(data)

        if errors:
            for err in errors:
                flash(err, 'error')
            return False

        sql = """
            INSERT INTO dentist (`D_ID`,`Name`,`Specialization`, `Contact`, `Experience`)
            VALUES (%s, %s, %s,%s,%s)
        """
        val = (
            cleaned_data['dentist_id'],
            cleaned_data['name'],
            cleaned_data['specialization'],
            cleaned_data['contact'],
            cleaned_data['experience']
        )

        cursor.execute(sql, val)
        conn.commit()
        flash("Dentist added successfully!", "success")
        logging.info(f"Dentist {cleaned_data['name']} added with ID {cleaned_data['dentist_id']}")
        return True

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        flash(f"Database error occurred: {err}", "error")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Database connection closed.")

            
            
    
   
def delete_dentist_db(dentist_id):
    conn = db_connect()  # Use role-based DB connection
    cursor = conn.cursor()

    try:
        sql = "DELETE FROM dentist WHERE `D_ID` = %s "
        val = (dentist_id,)
        cursor.execute(sql, val)
        conn.commit()
        print(cursor.rowcount, "record deleted.")
    except Exception as e:
        print("Error deleting dentist:", e)
    finally:
        cursor.close()
        conn.close()
        
        
    
def display_dentist_db():
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    try:
        
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM dentist"
        cursor.execute(sql)
        result = cursor.fetchall()

    except mysql.connector.Error as err:
        logging.error(f"Error fetching appointments: {err}")
        html += "<p>Error loading appointments.</p>"

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    # Generate HTML table
    if result:
        html += "<table style='border-collapse: collapse; width: 70%;'>\n"
        html += "<tr style='background-color: #333; color: white;'>\n"
        html += "<th style='padding: 10px;'>D_ID</th>\n"
        html += "<th style='padding: 10px;'>Name</th>\n"
        html += "<th style='padding: 10px;'>Specialization</th>\n"
        html += "<th style='padding: 10px;'>Contact</th>\n"
        html += "<th style='padding: 10px;'>Experience</th>\n"
        
        html += "</tr>\n"

        for row in result:
            html += "<tr style='background-color: #f2f2f2;'>\n"
            html += f"<td style='padding: 10px;'>{row['D_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Name']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Specialization']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Contact']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Experience']}</td>\n"
            
            html += "</tr>\n"

        html += "</table>"
    else:
        html += "<p>No dentist found.</p>"

    return html

# functios for treatment

def validate_treatment_data(data):
    """Validate and clean treatment data."""
    errors = []
    cleaned_data = {}

    # Validate and clean treatment ID
    treatment_id = data.get('treatment_id', '').strip()
    if not re.match(r'^[A-Za-z0-9]+$', treatment_id):
        errors.append("Invalid Treatment ID: Only letters and numbers allowed.")
    cleaned_data['treatment_id'] = treatment_id

    # Validate and clean treatment name (USE clean_text here)
    treatment_name = data.get('treatment_name', '').strip()
    if treatment_name:
        cleaned_data['treatment_name'] = clean_text(treatment_name)
    else:
        errors.append("Treatment name cannot be empty.")

    # Validate description (optional but clean it - USE clean_text here)
    description = data.get('description', '').strip()
    cleaned_data['description'] = clean_text(description) if description else ''

    # Validate cost (must be a positive number)
    cost = data.get('cost', '').strip()
    if not cost.replace('.', '', 1).isdigit() or float(cost) < 0:
        errors.append("Invalid Cost: Must be a positive number.")
    cleaned_data['cost'] = float(cost) if cost.replace('.', '', 1).isdigit() else None

    return errors, cleaned_data

    return errors, cleaned_data


def add_treatment_db(data):
    try:
        errors, cleaned_data = validate_treatment_data(data)
        if errors:
            print("Errors found:", errors)
            return

        conn = db_connect()
        cursor = conn.cursor()

        sql = "INSERT INTO treatment (`T_ID`,`Name`,`Description`, `Cost`) VALUES (%s, %s, %s, %s)"
        val = (
            cleaned_data['treatment_id'],
            cleaned_data['treatment_name'],
            cleaned_data['description'],
            cleaned_data['cost']
        )

        cursor.execute(sql, val)
        conn.commit()
        print(cursor.rowcount, "treatment inserted.")

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Connection closed.")

    
    
    
def delete_treatment_db(treatment_id):
    conn = db_connect()  
    cursor = conn.cursor()

    try:
        sql = "DELETE FROM treatment WHERE `T_ID` = %s "
        val = (treatment_id,)
        cursor.execute(sql, val)
        conn.commit()
        print(cursor.rowcount, "record deleted.")
    except Exception as e:
        print("Error deleting treatment:", e)
    finally:
        cursor.close()
        conn.close()
 
 
def display_treatment_db():
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    try:
        
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM treatment"
        cursor.execute(sql)
        result = cursor.fetchall()

    except mysql.connector.Error as err:
        logging.error(f"Error fetching appointments: {err}")
        html += "<p>Error loading treatment.</p>"

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    # Generate HTML table
    if result:
        html += "<table style='border-collapse: collapse; width: 70%;'>\n"
        html += "<tr style='background-color: #333; color: white;'>\n"
        html += "<th style='padding: 10px;'>T_ID</th>\n"
        html += "<th style='padding: 10px;'>Name</th>\n"
        html += "<th style='padding: 10px;'>Description</th>\n"
        html += "<th style='padding: 10px;'>Cost</th>\n"
        
        html += "</tr>\n"

        for row in result:
            html += "<tr style='background-color: #f2f2f2;'>\n"
            html += f"<td style='padding: 10px;'>{row['T_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Name']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Description']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Cost']}</td>\n"
            
            html += "</tr>\n"

        html += "</table>"
    else:
        html += "<p>No treatment found.</p>"

    return html
 
 
# Funcion for payment  

def add_payment_db(data):
    try:
       
        conn = db_connect()
        cursor = conn.cursor()

        sql = "INSERT INTO payment (`PM_ID`,`P_ID`,`AP_ID`,`Amount`,`Method`, `Status`, `Date`) VALUES (%s, %s, %s,%s,%s,%s,%s)"
        val = (data['payment_id'],data['patient_id'],data['appointment_id'],data['amount'],data['method'], data['status'], data['date'])

        cursor.execute(sql, val)
        conn.commit()
        print(cursor.rowcount, "payment inserted.")

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Connection closed.")
            
            
            
def update_payment_db():
    payment_id = request.form['payment_id']
    new_status = request.form['status']
    method = request.form['method']
    date = request.form['date']

    conn = db_connect()
    cursor = conn.cursor()

    try:
        sql = "UPDATE payment SET Status = %s, Method = %s, Date = %s WHERE P_ID = %s"
        val = (new_status, method, date, payment_id)
        cursor.execute(sql, val)
        conn.commit()
        flash("Payment updated successfully!", "success")
    except Exception as e:
        print("Error updating payment:", e)
        flash("Failed to update payment.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('payment'))



def display_payment_db():
    result = None
    html = "<div style='margin-bottom: 100px;'></div>"

    try:
        
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM payment"
        cursor.execute(sql)
        result = cursor.fetchall()

    except mysql.connector.Error as err:
        logging.error(f"Error fetching payments: {err}")
        html += "<p>Error loading treatment.</p>"

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    # Generate HTML table
    if result:
        html += "<table style='border-collapse: collapse; width: 70%;'>\n"
        html += "<tr style='background-color: #333; color: white;'>\n"
        html += "<th style='padding: 10px;'>PM_ID</th>\n"
        html += "<th style='padding: 10px;'>P_ID</th>\n"
        html += "<th style='padding: 10px;'>AP_ID</th>\n"
        html += "<th style='padding: 10px;'>Amount</th>\n"
        html += "<th style='padding: 10px;'>Method</th>\n"
        html += "<th style='padding: 10px;'>Status</th>\n"
        html += "<th style='padding: 10px;'>Date</th>\n"
        html += "</tr>\n"

        for row in result:
            html += "<tr style='background-color: #f2f2f2;'>\n"
            html += f"<td style='padding: 10px;'>{row['PM_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['P_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['AP_ID']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Amount']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Method']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Status']}</td>\n"
            html += f"<td style='padding: 10px;'>{row['Date']}</td>\n"
            html += "</tr>\n"

        html += "</table>"
    else:
        html += "<p>No payment found.</p>"

    return html



  # for session security
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        try:
            # Try to connect directly with user credentials
            conn = mysql.connector.connect(
                host='localhost',
                user=username,
                password=password,
                database='CLINIC'
            )

            if conn.is_connected():
                session['db_username'] = username
                session['db_password'] = password
                session['role'] = role

                if role == 'admin':
                    return render_template('admin_dashboard.html')
                elif role == 'frontdesk':
                    return render_template('frontdesk_dashboard.html')
                else:
                    flash('Invalid role.', 'error')
                    return redirect(url_for('login'))

        except mysql.connector.Error as err:
            flash('Invalid credentials.', 'error')
            return redirect(url_for('login'))
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    return render_template('login.html')








@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')



@app.route('/frontdesk_dashboard')
def frontdesk_dashboard():
    if session.get('role') != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('frontdesk_dashboard.html')




@app.route('/appointment')
def appointment():
    role = session.get('role')
    if role not in ['frontdesk', 'dentist']:
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('appointment.html')





@app.route('/add_appoint')
def add_appoint():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('add_appointment.html')

# Route to handle add appointment form submission
@app.route('/add_appoint', methods=['POST']) 
def add_appointment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    data = request.form 
    success = add_appointment_db(data)  # Now checking success

    if success:
        return render_template('appointment.html')
    else:
        return redirect(url_for('add_appoint'))




@app.route('/update_appoint')
def update_appoint():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('update_appointment.html')


@app.route('/update_appoint', methods=['POST']) 
def update_appointment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    global data
    data = request.form 
    update_appoint_db()  # Make sure your db function accepts `role`
    
    print("updated appointment")
    return render_template('appointment.html')



@app.route('/all_appoint')
def all_appoint():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = all_appoint_db()  # Pass role to DB function
    return render_template('all_appointments.html', table=table_html)


@app.route('/all_appoint', methods=['POST']) 
def all_appointment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = all_appoint_db()  # Pass role to DB function
    print("Showed all appointments")
    return render_template('all_appointments.html', table=table_html)




@app.route('/today_appoint')
def today_appoint():
    role = session.get('role')
    if role not in ['frontdesk', 'admin']:
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    return render_template('today_appointment.html')


@app.route('/today_appoint', methods=['POST']) 
def today_appointment_def(): 
    role = session.get('role')
    if role not in ['frontdesk', 'admin']:
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    data = request.form
    table_html = today_appoint_db(data)  # Updated function call with role
    print("Showed today's appointment")
    return render_template('today_appointment.html', table=table_html)



#routing for patient functions

@app.route('/patient')
def patient():
    role = session.get('role')
    if role !='admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('patients.html')


@app.route('/add_patient', methods=['GET'])
def add_patient():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('add_patient.html')


@app.route('/add_patient', methods=['POST'])
def add_patient_submit():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    data = request.form
    if add_patient_db(data):
        flash("Patient added successfully!", "success")
        return redirect(url_for('display_patient'))
    else:
        # If add_patient_db returns False (due to errors), redirect back to the GET route
        return redirect(url_for('add_patient'))


@app.route('/delete_patient')
def delete_patient():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('delete_patient.html')


@app.route('/delete_patient', methods=['POST']) 
def delete_patient_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    patient_id = request.form['patient_id']  
    delete_patient_db(patient_id)  # Pass role if needed
    print("Deleted patient")
    return render_template('patients.html')


@app.route('/display_patient')
def display_patient():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    # No need to pass role anymore as display_patient_db() does not require it
    table_html = display_patient_db()  
    return render_template('display_patient.html', table=table_html)


@app.route('/display_patient', methods=['POST']) 
def display_patient_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    # Again, no need to pass role to display_patient_db
    table_html = display_patient_db()
    print("Showed all patients")
    return render_template('display_patient.html', table=table_html)


# Dentist functions

@app.route('/dentist')
def dentist():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('dentists.html')


@app.route('/add_dentist', methods=['GET'])
def add_dentist():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('add_dentist.html')

@app.route('/add_dentist', methods=['POST'])
def add_dentist_submit():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    data = request.form
    if add_dentist_db(data):
        return redirect(url_for('dentist')) # Redirect to dentist list on success
    else:
        return redirect(url_for('add_dentist'))

@app.route('/delete_dentist')
def delete_dentist():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('delete_dentist.html')


@app.route('/delete_dentist', methods=['POST']) 
def delete_dentist_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    dentist_id = request.form['dentist_id']
    delete_dentist_db(dentist_id)  # Pass role if needed
    print("Deleted dentist")
    return render_template('dentists.html')


@app.route('/display_dentist')
def display_dentist():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_dentist_db()
    return render_template('display_dentist.html', table=table_html)


@app.route('/display_dentist', methods=['POST']) 
def display_dentist_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_dentist_db()
    print("Showed all dentists")
    return render_template('display_dentist.html', table=table_html)



# Routings for treatment

@app.route('/treatment')
def treatment():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('treatment.html')


@app.route('/add_treatment')
def add_treatment():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('add_treatment.html')


@app.route('/add_treatment', methods=['POST']) 
def add_treatment_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    global data
    data = request.form 
    add_treatment_db(data)  # Pass role if needed
    print("Added treatment")
    return render_template('add_treatment.html')


@app.route('/delete_treatment')
def delete_treatment():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('delete_treatment.html')


@app.route('/delete_treatment', methods=['POST']) 
def delete_treatment_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    treatment_id = request.form['treatment_id']
    delete_treatment_db(treatment_id)
    print("Deleted treatment")
    return render_template('treatment.html')


@app.route('/display_treatment')
def display_treatment():
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_treatment_db()
    return render_template('display_treatment.html', table=table_html)


@app.route('/display_treatment', methods=['POST']) 
def display_treatment_def(): 
    role = session.get('role')
    if role != 'admin':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_treatment_db()
    print("Showed all treatments")
    return render_template('display_treatment.html', table=table_html)


# routing for payment


@app.route('/payment')
def payment():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('payment.html')


@app.route('/add_payment')
def add_payment():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('add_payment.html')


@app.route('/add_payment', methods=['POST']) 
def add_payment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    global data
    data = request.form 
    add_payment_db(data)  # pass role if needed
    print("Added payment")
    return render_template('payment.html')


@app.route('/update_payment')
def update_payment():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))
    return render_template('update_payment.html')


@app.route('/update_payment', methods=['POST']) 
def update_payment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    global data
    data = request.form 
    update_payment_db()
    print("Updated payment")
    return render_template('payment.html')


@app.route('/display_payment')
def display_payment():
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_payment_db()
    return render_template('display_payment.html', table=table_html)


@app.route('/display_payment', methods=['POST']) 
def display_payment_def(): 
    role = session.get('role')
    if role != 'frontdesk':
        flash("Access denied.", "error")
        return redirect(url_for('login'))

    table_html = display_payment_db(role)
    print("Showed all payments")
    return render_template('display_payment.html', table=table_html)



if __name__ == '__main__': 

    app.run(debug=True,host='0.0.0.0',port=7000)


    
  



