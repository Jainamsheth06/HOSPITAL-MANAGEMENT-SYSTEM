import os
import django
from datetime import date, time as dtime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_project.settings')
django.setup()

from django.contrib.auth.models import User
from hms_app.models import Department, DoctorProfile, PatientProfile, Appointment
from hms_app.notifications import (
    notify_patient_registered,
    notify_doctor_registered,
    notify_staff_registered,
    notify_appointment_booked,
    notify_appointment_rescheduled,
    notify_appointment_cancelled,
)

target_email = "sheth.jainam.coder@gmail.com"
print(f" Sending ALL 6 notification email types to: {target_email}...\n")

# Mock User & Profiles
user_pat = User(username="jainam_patient", first_name="Jainam", last_name="Sheth", email=target_email)
patient = PatientProfile(user=user_pat, patient_id="PAT-2026-9901", blood_group="O+", phone="+91 98765 43210")

dept = Department(name="Cardiology & Heart Care")
user_doc = User(username="dr_rajesh", first_name="Rajesh", last_name="Patel", email=target_email)
doctor = DoctorProfile(user=user_doc, department=dept, specialization="Senior Cardiologist", consultation_fee=750.00)

user_staff = User(username="priya_staff", first_name="Priya", last_name="Sharma", email=target_email)

apt = Appointment(
    id=1024,
    patient=patient,
    doctor=doctor,
    appointment_date=date(2026, 9, 25),
    time_slot=dtime(10, 30),
    reason="Routine Cardiac Health Checkup",
    status="SCHEDULED"
)

# 1. Patient Registration Email
print("1. Sending Patient Registration Email...")
notify_patient_registered(patient, raw_password="PatientPass@2026")

# 2. Doctor Registration Email
print("2. Sending Doctor Registration Email...")
notify_doctor_registered(doctor, raw_password="DoctorSecure@2026")

# 3. Staff Registration Email
print("3. Sending Staff Registration Email...")
notify_staff_registered(user_staff, raw_password="StaffPass@2026")

# 4. Appointment Booking Email
print("4. Sending Appointment Booking Confirmation...")
notify_appointment_booked(apt)

# 5. Appointment Rescheduled Email
print("5. Sending Appointment Rescheduled Notice...")
notify_appointment_rescheduled(apt, old_date="2026-09-22", old_time="09:00 AM")

# 6. Appointment Cancelled Email
print("6. Sending Appointment Cancellation Notice...")
notify_appointment_cancelled(apt)

print("\n ALL 6 EMAILS SUCCESSFULLY DISPATCHED!")
