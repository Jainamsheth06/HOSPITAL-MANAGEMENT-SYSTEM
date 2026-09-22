import datetime
from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PatientProfile, DoctorProfile, Appointment, MedicalRecord

TIME_SLOT_CHOICES = [
    ('09:00:00', '09:00 AM'),
    ('09:30:00', '09:30 AM'),
    ('10:00:00', '10:00 AM'),
    ('10:30:00', '10:30 AM'),
    ('11:00:00', '11:00 AM'),
    ('11:30:00', '11:30 AM'),
    ('12:00:00', '12:00 PM'),
    ('12:30:00', '12:30 PM'),
    ('14:00:00', '02:00 PM'),
    ('14:30:00', '02:30 PM'),
    ('15:00:00', '03:00 PM'),
    ('15:30:00', '03:30 PM'),
    ('16:00:00', '04:00 PM'),
    ('16:30:00', '04:30 PM'),
    ('17:00:00', '05:00 PM'),
]

import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

BAD_WORDS_LIST = ['admin', 'root', 'superuser', 'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'idiot']

def contains_bad_words(text):
    if not text:
        return False
    text = text.lower()
    for word in BAD_WORDS_LIST:
        if word in text:
            return True
    return False

def validate_email_address(email):
    if not email:
        raise ValidationError("Email address is required.")
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Please enter a valid working email address (e.g. name@gmail.com).")
    parts = email.split('@')
    domain = parts[1]
    if '.' not in domain or len(domain.split('.')[-1]) < 2:
        raise ValidationError("Please enter a valid email domain (e.g. gmail.com).")
    return email.lower()

class PatientRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}))
    gender = forms.ChoiceField(choices=PatientProfile.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    blood_group = forms.ChoiceField(choices=PatientProfile.BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))
    emergency_contact = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-input'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}), required=False)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        cd = self.cleaned_data
        
        bad_words_found = contains_bad_words(cd['username']) or contains_bad_words(cd['first_name']) or contains_bad_words(cd['last_name'])
        
        user = User.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            first_name=cd['first_name'],
            last_name=cd['last_name']
        )
        
        if bad_words_found:
            user.is_active = False
            user.save()
            from .notifications import send_restricted_account_alert
            send_restricted_account_alert(cd['email'], cd['username'], f"{cd['first_name']} {cd['last_name']}")
            
        patient_group, _ = Group.objects.get_or_create(name='Patients')
        user.groups.add(patient_group)

        patient = PatientProfile.objects.create(
            user=user,
            date_of_birth=cd['date_of_birth'],
            gender=cd['gender'],
            blood_group=cd['blood_group'],
            emergency_contact=cd['emergency_contact'],
            phone=cd['phone'],
            address=cd['address']
        )
        return patient

class AppointmentBookingForm(forms.ModelForm):
    time_slot = forms.ChoiceField(choices=TIME_SLOT_CHOICES, widget=forms.Select(attrs={'class': 'form-input'}))

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'time_slot', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-input'}),
            'doctor': forms.Select(attrs={'class': 'form-input'}),
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        time_slot_str = cleaned_data.get('time_slot')

        if appointment_date and appointment_date < timezone.now().date():
            self.add_error('appointment_date', "Cannot book appointments for past dates.")

        if doctor and appointment_date and time_slot_str:
            time_parts = [int(x) for x in time_slot_str.split(':')]
            t_slot = datetime.time(time_parts[0], time_parts[1], time_parts[2])
            cleaned_data['time_slot'] = t_slot

            conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                time_slot=t_slot,
                status='SCHEDULED'
            ).exists()

            if conflict:
                self.add_error('time_slot', f"Dr. {doctor.user.last_name or doctor.user.username} is already booked at {t_slot.strftime('%I:%M %p')} on {appointment_date}.")

        return cleaned_data

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['symptoms', 'diagnosis', 'prescription', 'consultation_fee', 'medicine_fee', 'is_paid', 'follow_up_date']
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'prescription': forms.Textarea(attrs={'rows': 4, 'class': 'form-input', 'placeholder': 'e.g., Paracetamol 500mg - 1 tab twice daily after meals (5 days)'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'medicine_fee': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

class DoctorRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    # Doctor Profile specific fields
    from .models import Department
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-input'}))
    specialization = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    consultation_fee = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0.00, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        cd = self.cleaned_data
        
        bad_words_found = contains_bad_words(cd['username']) or contains_bad_words(cd['first_name']) or contains_bad_words(cd['last_name'])
        
        user = User.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            first_name=cd['first_name'],
            last_name=cd['last_name']
        )
        
        if bad_words_found:
            user.is_active = False
            user.save()
            from .notifications import send_restricted_account_alert
            send_restricted_account_alert(cd['email'], cd['username'], f"{cd['first_name']} {cd['last_name']}")
            
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        user.groups.add(doctor_group)

        doctor = DoctorProfile.objects.create(
            user=user,
            department=cd['department'],
            specialization=cd['specialization'],
            consultation_fee=cd['consultation_fee'],
            phone=cd['phone']
        )
        return doctor

class ReceptionistRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self):
        cd = self.cleaned_data
        
        bad_words_found = contains_bad_words(cd['username']) or contains_bad_words(cd['first_name']) or contains_bad_words(cd['last_name'])
        
        user = User.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            first_name=cd['first_name'],
            last_name=cd['last_name']
        )
        
        if bad_words_found:
            user.is_active = False
            user.save()
            from .notifications import send_restricted_account_alert
            send_restricted_account_alert(cd['email'], cd['username'], f"{cd['first_name']} {cd['last_name']}")
            
        receptionist_group, _ = Group.objects.get_or_create(name='Receptionists')
        user.groups.add(receptionist_group)
        return user
