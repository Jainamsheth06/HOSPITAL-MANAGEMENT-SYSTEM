import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_project.settings')
django.setup()

from django.contrib.auth.models import User
from hms_app.models import PatientProfile
from hms_app.notifications import notify_patient_registered

target_email = "jainamsheth2006@gmail.com"
print(f"Sending Trial Patient Registration Email to: {target_email}...")

user = User(
    username="jainam_sheth_test",
    first_name="Jainam",
    last_name="Sheth",
    email=target_email
)
patient = PatientProfile(
    user=user,
    patient_id="PAT-2026-7788",
    blood_group="O+",
    phone="+91 98765 43210"
)

res = notify_patient_registered(patient, raw_password="JainamPass@2026")
print(" Dispatch finished successfully!")
