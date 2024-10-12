from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
import schedule
import time
import threading
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS
from twilio.rest import Client
import logging

app = Flask(__name__, template_folder='templates')
CORS(app)

executor = ThreadPoolExecutor()
db_path = "appointments.db"

# Twilio configuration
TWILIO_ACCOUNT_SID = 'ACe13a3c75c3f37fefe54221dce79d08ed'
TWILIO_AUTH_TOKEN = '4dd8c566c3dd403f7b2b411e1f9de221'
TWILIO_PHONE_NUMBER = 'MG5937880fe6180b23e0d5cfde64cad866'
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Create Database
def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                patient_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                reminder_sent INTEGER DEFAULT 0,
                phone_number TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                hospital_id INTEGER,
                available_days TEXT NOT NULL,
                available_times TEXT NOT NULL,
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id))''')
    conn.commit()
    conn.close()

# Add Mumbai Hospitals and Doctors Data
def add_initial_data():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Adding Hospitals
    hospitals = [
        (1, "Mumbai City Hospital", "123 Mumbai Street, Mumbai"),
        (2, "Mumbai Health Clinic", "456 Health Road, Mumbai"),
        (3, "Fortis Hospital Mumbai", "789 Fortis Avenue, Mumbai"),
        (4, "Lilavati Hospital", "101 Lilavati Street, Mumbai"),
        (5, "Hiranandani Hospital", "202 Hiranandani Gardens, Mumbai"),
        (6, "Kokilaben Hospital", "303 Kokilaben Road, Mumbai"),
        (7, "Breach Candy Hospital", "404 Breach Candy Area, Mumbai"),
        (8, "Nanavati Hospital", "505 Nanavati Avenue, Mumbai"),
        (9, "Holy Spirit Hospital", "606 Holy Spirit Lane, Mumbai"),
        (10, "Saifee Hospital", "707 Saifee Street, Mumbai"),
        (11, "Seven Hills Hospital", "808 Seven Hills Drive, Mumbai"),
        (12, "Jaslok Hospital", "909 Jaslok Boulevard, Mumbai"),
        (13, "S L Raheja Hospital", "111 Raheja Lane, Mumbai"),
        (14, "Wockhardt Hospital", "222 Wockhardt Street, Mumbai"),
        (15, "Bombay Hospital", "333 Bombay Road, Mumbai"),
        (16, "Bhatia Hospital", "444 Bhatia Lane, Mumbai"),
        (17, "Global Hospital", "555 Global Avenue, Mumbai"),
        (18, "Apollo Spectra", "666 Apollo Street, Mumbai"),
        (19, "CritiCare Hospital", "777 CritiCare Drive, Mumbai"),
        (20, "SRCC Children's Hospital", "888 SRCC Street, Mumbai")
    ]
    c.executemany("INSERT OR IGNORE INTO hospitals (id, name, address) VALUES (?, ?, ?)", hospitals)

    # Adding Doctors
    doctors = [
        (1, "Dr. A. Sharma", "Cardiologist", 1, "Monday, Wednesday, Friday", "10:00-14:00"),
        (2, "Dr. B. Patel", "Dermatologist", 2, "Tuesday, Thursday", "12:00-16:00"),
        (3, "Dr. C. Rao", "General Physician", 3, "Monday to Friday", "09:00-13:00"),
        (4, "Dr. D. Mehta", "Orthopedic", 4, "Monday, Thursday", "14:00-18:00"),
        (5, "Dr. E. Kulkarni", "Pediatrician", 5, "Wednesday, Saturday", "10:00-15:00"),
        (6, "Dr. F. Gupta", "Neurologist", 6, "Tuesday, Friday", "11:00-15:00"),
        (7, "Dr. G. Joshi", "ENT Specialist", 7, "Monday, Wednesday", "10:00-13:00"),
        (8, "Dr. H. Desai", "Gastroenterologist", 8, "Thursday, Saturday", "14:00-18:00"),
        (9, "Dr. I. Nair", "Oncologist", 9, "Tuesday, Friday", "09:00-12:00"),
        (10, "Dr. J. Singh", "Urologist", 10, "Monday, Thursday", "13:00-17:00"),
        (11, "Dr. K. Khan", "Cardiologist", 11, "Wednesday, Saturday", "10:00-14:00"),
        (12, "Dr. L. Roy", "Dermatologist", 12, "Monday, Friday", "11:00-15:00"),
        (13, "Dr. M. Shetty", "General Physician", 13, "Monday to Friday", "08:00-12:00"),
        (14, "Dr. N. Tiwari", "Orthopedic", 14, "Tuesday, Thursday", "15:00-19:00"),
        (15, "Dr. O. Verma", "Pediatrician", 15, "Wednesday, Saturday", "09:00-13:00"),
        (16, "Dr. P. Bhat", "Neurologist", 16, "Monday, Thursday", "10:00-14:00"),
        (17, "Dr. Q. Shah", "ENT Specialist", 17, "Tuesday, Friday", "12:00-16:00"),
        (18, "Dr. R. Iyer", "Gastroenterologist", 18, "Monday, Wednesday", "14:00-18:00"),
        (19, "Dr. S. Kaur", "Oncologist", 19, "Thursday, Saturday", "09:00-12:00"),
        (20, "Dr. T. Menon", "Urologist", 20, "Tuesday, Friday", "10:00-14:00")
    ]
    c.executemany("INSERT OR IGNORE INTO doctors (id, name, specialty, hospital_id, available_days, available_times) VALUES (?, ?, ?, ?, ?, ?)", doctors)

    conn.commit()
    conn.close()

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Get Hospitals
@app.route('/get_hospitals', methods=['GET'])
def get_hospitals():
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id, name FROM hospitals")
        hospitals = [{"id": row[0], "name": row[1]} for row in c.fetchall()]
        conn.close()
        return jsonify(hospitals)
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500

# Get Doctors by Hospital ID
@app.route('/get_doctors', methods=['GET'])
def get_doctors():
    try:
        hospital_id = request.args.get('hospital_id')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, specialty FROM doctors WHERE hospital_id = ?", (hospital_id,))
        doctors = [{"id": row[0], "name": row[1], "specialty": row[2]} for row in c.fetchall()]
        conn.close()
        return jsonify(doctors)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

logging.basicConfig(level=logging.DEBUG)

# Schedule Appointment (Async)
@app.route('/schedule', methods=['POST'])
async def schedule_appointment():
    try:
        data = request.get_json()
        logging.debug(f"Received data: {data}")
        patient_id = data.get('patient_id')
        patient_name = data.get('patient_name')
        doctor_name = data.get('doctor_name')
        appointment_time = data.get('appointment_time')
        phone_number = f'+91{data.get("phone_number")}'
        # Check for missing data
        if not all([patient_id, patient_name, doctor_name, appointment_time, phone_number]):
            raise ValueError("Missing required fields in request data.")

        appointment_datetime = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, schedule_appointment_sync, patient_id, patient_name, doctor_name, appointment_time, phone_number)

        appointment_day = appointment_datetime.strftime('%A')
        appointment_date = appointment_datetime.strftime('%Y-%m-%d')
        return jsonify({
            "message": f"Appointment scheduled successfully with Dr. {doctor_name} on {appointment_day}, {appointment_date} at {appointment_datetime.strftime('%H:%M')}"
        }), 201
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500

# Synchronous function to handle DB insert
def schedule_appointment_sync(patient_id, patient_name, doctor_name, appointment_time, phone_number):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO appointments (patient_id, patient_name, doctor_name, appointment_time, phone_number) VALUES (?, ?, ?, ?, ?)",
              (patient_id, patient_name, doctor_name, appointment_time, phone_number))
    conn.commit()
    appointment_id = c.lastrowid 
    conn.close()
    
    try:
        message = client.messages.create(
            body=f"Appointment scheduled with Dr. {doctor_name} on {appointment_time}. Your appointment ID is {appointment_id}.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    except Exception as e:
        print(f"Failed to send SMS: {e}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO appointments (patient_id, patient_name, doctor_name, appointment_time, phone_number) VALUES (?, ?, ?, ?, ?)",
              (patient_id, patient_name, doctor_name, appointment_time, phone_number))
    conn.commit()
    conn.close()
    
    # Send confirmation SMS using Twilio
    try:
        message = client.messages.create(
            body=f"Appointment scheduled with Dr. {doctor_name} on {appointment_time}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    except Exception as e:
        print(f"Failed to send SMS: {e}")

# Reschedule Appointment
@app.route('/reschedule', methods=['PUT'])
async def reschedule_appointment():
    try:
        data = request.get_json()
        appointment_id = data['appointment_id']
        new_time = data['new_time']

        new_datetime = datetime.strptime(new_time, "%Y-%m-%d %H:%M")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, reschedule_appointment_sync, appointment_id, new_time)

        return jsonify({"message": "Appointment rescheduled successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Synchronous function to handle DB update
def reschedule_appointment_sync(appointment_id, new_time):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE appointments SET appointment_time = ? WHERE id = ?", (new_time, appointment_id))
    conn.commit()
    conn.close()

# Cancel Appointment
@app.route('/cancel', methods=['DELETE'])
async def cancel_appointment():
    try:
        data = request.get_json()
        appointment_id = data['appointment_id']

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(executor, cancel_appointment_sync, appointment_id)

        return jsonify({"message": "Appointment canceled successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Synchronous function to handle DB delete
def cancel_appointment_sync(appointment_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

# Function to send reminders (Async)
async def send_reminder(appointment_id, patient_name, doctor_name, appointment_time, phone_number):
    reminder_message = f"Reminder: {patient_name}, you have an appointment with Dr. {doctor_name} at {appointment_time}."
    print(reminder_message)
    
    
    try:
        client.messages.create(
            body=reminder_message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    except Exception as e:
        print(f"Failed to send reminder SMS: {e}")
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, update_reminder_status_sync, appointment_id)


def update_reminder_status_sync(appointment_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

# Check for appointments that need reminders
async def check_appointments():
    while True:
        await asyncio.sleep(60)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        now = datetime.now()
        reminder_time = now + timedelta(hours=24)
        try:
            c.execute("SELECT * FROM appointments WHERE reminder_sent = 0")
            appointments = c.fetchall()

            for appointment in appointments:
                appointment_id, patient_id, patient_name, doctor_name, appointment_time_str, reminder_sent, phone_number = appointment
                appointment_time = datetime.strptime(appointment_time_str, "%Y-%m-%d %H:%M")
                if now < appointment_time <= reminder_time:
                    await send_reminder(appointment_id, patient_name, doctor_name, appointment_time_str, phone_number)
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

# Start the reminder check task
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.create_task(check_appointments())

if __name__ == '__main__':
    if sys.platform == "win32":
        venv_path = os.path.join(os.getcwd(), 'venv', 'Scripts', 'activate')
    else:
        venv_path = os.path.join(os.getcwd(), 'venv', 'bin', 'activate')

    if not os.path.exists('venv'):
        os.system('python -m venv venv')
        print(f"Virtual environment created. Activate it using: source {venv_path}")
    else:
        print(f"Virtual environment already exists. Activate it using: source {venv_path}")
    
    init_db()
    add_initial_data()
    app.run(debug=True, use_reloader=False)