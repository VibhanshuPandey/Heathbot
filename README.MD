## Doctor Appointment Scheduler Chatbot

This is a simple chatbot application for scheduling, rescheduling, or canceling doctor appointments. Users can interact with the chatbot via a web interface to manage their appointments easily.

### Features
- Schedule an appointment with a doctor.
- Reschedule an existing appointment.
- Cancel an appointment.

### Technologies Used
- HTML, CSS, JavaScript (Frontend)
- Python (Backend)
- SQLite (Database)

### How to Run the Application
1. Clone the repository:
   ```sh
   git clone https://github.com/VibhanshuPandey/Heathbot.git
   ```
2. Navigate to the project directory:
   ```sh
   cd doctor-appointment-scheduler
   ```
3. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```
4. Run the backend server:
   ```sh
   python bot.py
   ```
5. Open `index.html` in a browser to use the chatbot interface.

### Endpoints
- `/get_hospitals`: Returns the list of available hospitals.
- `/get_doctors?hospital_id=<hospital_id>`: Returns the list of doctors for the selected hospital.
- `/schedule`: Schedules a new appointment.
- `/reschedule`: Reschedules an existing appointment.
- `/cancel`: Cancels an appointment.

### License
This project is licensed under the MIT License.