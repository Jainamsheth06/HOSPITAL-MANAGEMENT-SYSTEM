import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from hms_app.models import Department, DoctorProfile, PatientProfile, Appointment, MedicalRecord

class Command(BaseCommand):
    help = 'Seed initial demo departments, doctors, receptionists, patients, appointments, and records'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Core HMS initial data...")

        # 1. Create User Groups
        receptionist_group, _ = Group.objects.get_or_create(name='Receptionists')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        patient_group, _ = Group.objects.get_or_create(name='Patients')

        # 2. Create Superuser / Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@hospital.com', 'admin123')
            self.stdout.write("Created superuser 'admin' (password: admin123)")

        # 3. Create Receptionist User
        if not User.objects.filter(username='receptionist1').exists():
            rec_user = User.objects.create_user('receptionist1', 'rec@hospital.com', 'pass123', first_name='Clara', last_name='Oswald')
            rec_user.groups.add(receptionist_group)
            self.stdout.write("Created receptionist user 'receptionist1' (password: pass123)")

        # 4. Create Departments
        cardiology, _ = Department.objects.get_or_create(name='Cardiology', defaults={'description': 'Heart & Vascular Care'})
        neurology, _ = Department.objects.get_or_create(name='Neurology', defaults={'description': 'Brain & Nervous System'})
        ortho, _ = Department.objects.get_or_create(name='Orthopedics', defaults={'description': 'Bone & Joint Surgery'})
        general, _ = Department.objects.get_or_create(name='General Medicine', defaults={'description': 'Primary Care & Diagnostics'})

        # 5. Create Doctors
        dr1_user, created1 = User.objects.get_or_create(
            username='dr.smith',
            defaults={'email': 'smith@hospital.com', 'first_name': 'Arthur', 'last_name': 'Smith'}
        )
        if created1:
            dr1_user.set_password('pass123')
            dr1_user.save()
            dr1_user.groups.add(doctor_group)
        dr1_profile, _ = DoctorProfile.objects.get_or_create(
            user=dr1_user,
            defaults={'department': cardiology, 'specialization': 'Interventional Cardiology', 'consultation_fee': 500.00, 'phone': '9876500001'}
        )

        dr2_user, created2 = User.objects.get_or_create(
            username='dr.johnson',
            defaults={'email': 'johnson@hospital.com', 'first_name': 'Sarah', 'last_name': 'Johnson'}
        )
        if created2:
            dr2_user.set_password('pass123')
            dr2_user.save()
            dr2_user.groups.add(doctor_group)
        dr2_profile, _ = DoctorProfile.objects.get_or_create(
            user=dr2_user,
            defaults={'department': neurology, 'specialization': 'Clinical Neurology', 'consultation_fee': 700.00, 'phone': '9876500002'}
        )

        # 6. Create Patients
        p1_user, created_p1 = User.objects.get_or_create(
            username='john_doe',
            defaults={'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'}
        )
        if created_p1:
            p1_user.set_password('pass123')
            p1_user.save()
            p1_user.groups.add(patient_group)
        patient1, _ = PatientProfile.objects.get_or_create(
            user=p1_user,
            defaults={
                'date_of_birth': datetime.date(1988, 4, 12),
                'gender': 'M',
                'blood_group': 'O+',
                'emergency_contact': '9876543210',
                'phone': '9876543210',
                'address': '123 Elm Street, Cityville'
            }
        )

        p2_user, created_p2 = User.objects.get_or_create(
            username='jane_smith',
            defaults={'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'}
        )
        if created_p2:
            p2_user.set_password('pass123')
            p2_user.save()
            p2_user.groups.add(patient_group)
        patient2, _ = PatientProfile.objects.get_or_create(
            user=p2_user,
            defaults={
                'date_of_birth': datetime.date(1995, 9, 20),
                'gender': 'F',
                'blood_group': 'A+',
                'emergency_contact': '9123456789',
                'phone': '9123456789',
                'address': '456 Oak Avenue, Metropolis'
            }
        )

        # 7. Create Appointments
        today = timezone.now().date()
        apt1, _ = Appointment.objects.get_or_create(
            doctor=dr1_profile,
            appointment_date=today,
            time_slot=datetime.time(10, 0, 0),
            defaults={'patient': patient1, 'reason': 'Chest discomfort and shortness of breath', 'status': 'COMPLETED'}
        )

        apt2, _ = Appointment.objects.get_or_create(
            doctor=dr2_profile,
            appointment_date=today,
            time_slot=datetime.time(11, 30, 0),
            defaults={'patient': patient2, 'reason': 'Chronic migraine headaches', 'status': 'SCHEDULED'}
        )

        # 8. Create Medical Record for completed appointment
        MedicalRecord.objects.get_or_create(
            appointment=apt1,
            defaults={
                'symptoms': 'Mild exertional angina, fatigue for 3 days.',
                'diagnosis': 'Stage 1 Hypertension & Stress-induced Angina',
                'prescription': '1. Tab Amlodipine 5mg - 1-0-0 (30 Days)\n2. Tab Aspirin 75mg - 0-0-1 after dinner (30 Days)\n3. Reduced sodium intake diet and ECG re-check in 2 weeks.',
                'consultation_fee': 500.00,
                'medicine_fee': 350.00,
                'is_paid': True,
                'follow_up_date': today + datetime.timedelta(days=14)
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded database with demo hospital records!"))
