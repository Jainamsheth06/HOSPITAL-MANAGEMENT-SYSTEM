import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctors')
    specialization = models.CharField(max_length=100)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.00)])
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"Dr. {full_name} ({self.specialization})"

class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    )

    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    emergency_contact = models.CharField(max_length=15)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            year = timezone.now().year
            unique_suffix = str(uuid.uuid4().int)[:4]
            self.patient_id = f"PAT-{year}-{unique_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{self.patient_id} - {full_name}"

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'appointment_date', 'time_slot')
        ordering = ['appointment_date', 'time_slot']

    def clean(self):
        # Prevent past dates for new appointments
        if not self.pk and self.appointment_date and self.appointment_date < timezone.now().date():
            raise ValidationError({'appointment_date': 'Cannot schedule an appointment for a past date.'})

        # Conflict check: active appointment for doctor at same date and time
        existing = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            time_slot=self.time_slot,
            status='SCHEDULED'
        )
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError(f"Dr. {self.doctor.user.last_name or self.doctor.user.username} already has a scheduled appointment at {self.time_slot.strftime('%H:%M')} on {self.appointment_date}.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"APT #{self.id} | {self.patient.patient_id} with {self.doctor} on {self.appointment_date} at {self.time_slot.strftime('%H:%M')} [{self.status}]"

class MedicalRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    symptoms = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField(help_text="List medicines, dosage instructions, and duration")
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.00)])
    medicine_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_amount = (self.consultation_fee or 0) + (self.medicine_fee or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Medical Record for APT #{self.appointment.id} ({self.appointment.patient.patient_id})"
