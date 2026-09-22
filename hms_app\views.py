from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

import random
import json
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .models import PatientProfile, DoctorProfile, Appointment, MedicalRecord
from .forms import PatientRegistrationForm, AppointmentBookingForm, MedicalRecordForm, DoctorRegistrationForm, ReceptionistRegistrationForm
from .decorators import receptionist_required, doctor_required, patient_required
from .notifications import (
    notify_doctor_registered,
    notify_patient_registered,
    notify_appointment_booked,
    notify_staff_registered,
    notify_appointment_cancelled,
    notify_appointment_rescheduled,
    notify_medical_record_created,
    notify_record_deleted,
    send_password_reset_notification,
    send_password_reset_otp_email,
    send_password_reset_success_email
)

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'hms_app/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@receptionist_required
def doctor_register(request):
    if request.user.is_superuser:
        messages.error(request, "Access Denied: The Hospital Owner cannot register doctors. This is a Receptionist task.")
        return redirect('owner_dashboard')
        
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            raw_password = form.cleaned_data.get('password')
            doctor = form.save()
            # Send automated direct email with credentials to Doctor
            notify_doctor_registered(doctor, raw_password=raw_password)
            messages.success(request, f"Doctor {doctor.user.get_full_name() or doctor.user.username} registered successfully.")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorRegistrationForm()
        
    return render(request, 'hms_app/doctor_signup.html', {'form': form})


from django.contrib.auth.decorators import login_required, user_passes_test

def owner_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect('owner_dashboard')
    elif user.groups.filter(name='Receptionists').exists():
        return redirect('receptionist_dashboard')
    elif hasattr(user, 'doctor_profile') or user.groups.filter(name='Doctors').exists():
        return redirect('doctor_dashboard')
    elif hasattr(user, 'patient_profile') or user.groups.filter(name='Patients').exists():
        return redirect('patient_dashboard')
    return redirect('login')

# --- Owner Views ---
# Moved to owner_app/views.py

def receptionist_register(request):
    if request.user.is_superuser:
        messages.error(request, "Access Denied: The Hospital Owner cannot register staff.")
        return redirect('owner_dashboard')
    if request.user.is_authenticated and not request.user.is_superuser:
        return redirect('dashboard_redirect')
        
    if request.method == 'POST':
        form = ReceptionistRegistrationForm(request.POST)
        if form.is_valid():
            raw_password = form.cleaned_data.get('password')
            user = form.save()
            # Send automated direct email with credentials to Staff/Receptionist
            notify_staff_registered(user, raw_password=raw_password)
            messages.success(request, f"Receptionist {user.get_full_name() or user.username} registered successfully.")
            if request.user.is_superuser:
                return redirect('owner_dashboard')
            else:
                return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReceptionistRegistrationForm()
        
    return render(request, 'hms_app/receptionist_register.html', {'form': form})

# --- Receptionist Views ---

@receptionist_required
def receptionist_dashboard(request):
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(appointment_date=today).select_related('patient', 'doctor')
    total_patients = PatientProfile.objects.count()
    total_scheduled = Appointment.objects.filter(status='SCHEDULED').count()
    total_completed = Appointment.objects.filter(status='COMPLETED').count()
    
    context = {
        'today_date': today,
        'today_appointments': today_appointments,
        'total_patients': total_patients,
        'total_scheduled': total_scheduled,
        'total_completed': total_completed,
    }
    return render(request, 'hms_app/receptionist_dashboard.html', context)

@receptionist_required
def doctor_list(request):
    doctors = DoctorProfile.objects.select_related('user', 'department')
    return render(request, 'hms_app/doctor_list.html', {'doctors': doctors})

@owner_required
def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    username = doctor.user.username
    doc_name = doctor.user.get_full_name() or username
    doctor.user.delete()
    notify_record_deleted("Doctor", f"Dr. {doc_name} (@{username})", request.user.username)
    messages.success(request, f"Doctor '{username}' deleted successfully.")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('doctor_list')

@owner_required
def delete_patient(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    name = patient.user.get_full_name() or patient.user.username
    pat_code = patient.patient_id
    patient.user.delete()
    notify_record_deleted("Patient", f"{name} ({pat_code})", request.user.username)
    messages.success(request, f"Patient '{name}' deleted successfully.")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('patient_list')

@owner_required
def delete_appointment(request, appointment_id):
    apt = get_object_or_404(Appointment, id=appointment_id)
    apt_info = f"APT #{apt.id} ({apt.patient.patient_id} with Dr. {apt.doctor.user.last_name})"
    apt.delete()
    notify_record_deleted("Appointment", apt_info, request.user.username)
    messages.success(request, "Appointment deleted successfully.")
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('appointment_list')

@receptionist_required
def patient_register(request):
    if request.user.is_superuser:
        messages.error(request, "Access Denied: The Hospital Owner cannot register patients. This is a Receptionist task.")
        return redirect('owner_dashboard')
        
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            raw_password = form.cleaned_data.get('password')
            patient = form.save()
            # Send automated direct email with credentials to Patient
            notify_patient_registered(patient, raw_password=raw_password)
            messages.success(request, f"Patient {patient.patient_id} ({patient.user.get_full_name() or patient.user.username}) registered successfully.")
            return redirect('patient_detail', patient_id=patient.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientRegistrationForm()

    return render(request, 'hms_app/patient_register.html', {'form': form})

@receptionist_required
def patient_list(request):
    query = request.GET.get('q', '').strip()
    patients = PatientProfile.objects.select_related('user').all().order_by('-created_at')

    if query:
        patients = patients.filter(
            Q(patient_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'hms_app/patient_list.html', {'patients': patients, 'query': query})

@receptionist_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(PatientProfile.objects.select_related('user'), id=patient_id)
    appointments = patient.appointments.select_related('doctor__user', 'doctor__department').order_by('-appointment_date', '-time_slot')
    medical_records = MedicalRecord.objects.filter(appointment__patient=patient).select_related('appointment__doctor__user').order_by('-created_at')

    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    return render(request, 'hms_app/patient_detail.html', context)

@receptionist_required
def book_appointment(request):
    patient_id_param = request.GET.get('patient_id')
    initial_data = {}
    if patient_id_param:
        patient = get_object_or_404(PatientProfile, id=patient_id_param)
        initial_data['patient'] = patient

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            # Send automated direct email to Hospital Owner
            notify_appointment_booked(appointment)
            messages.success(request, f"Appointment #{appointment.id} scheduled successfully for {appointment.patient.user.get_full_name()} with {appointment.doctor}.")
            return redirect('appointment_list')
        else:
            messages.error(request, "Error booking appointment. Check slot availability or form errors.")
    else:
        form = AppointmentBookingForm(initial=initial_data)

    return render(request, 'hms_app/book_appointment.html', {'form': form})

@receptionist_required
def appointment_list(request):
    status_filter = request.GET.get('status', '').strip()
    doctor_filter = request.GET.get('doctor', '').strip()
    date_filter = request.GET.get('date', '').strip()

    appointments = Appointment.objects.select_related('patient__user', 'doctor__user', 'doctor__department').all().order_by('-appointment_date', '-time_slot')

    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    doctors = DoctorProfile.objects.select_related('user').all()

    context = {
        'appointments': appointments,
        'doctors': doctors,
        'status_filter': status_filter,
        'doctor_filter': doctor_filter,
        'date_filter': date_filter,
    }
    return render(request, 'hms_app/appointment_list.html', context)

@receptionist_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.status == 'COMPLETED':
        messages.error(request, "Completed appointments cannot be cancelled.")
    else:
        appointment.status = 'CANCELLED'
        appointment.save()
        # Send automated cancellation alert to Owner and Patient
        notify_appointment_cancelled(appointment)
        messages.success(request, f"Appointment #{appointment.id} has been cancelled.")
    return redirect('appointment_list')

@receptionist_required
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment.objects.select_related('patient__user', 'doctor__user'), id=appointment_id)
    if appointment.status == 'COMPLETED':
        messages.error(request, "Completed appointments cannot be rescheduled.")
        return redirect('appointment_list')
        
    old_date = appointment.appointment_date.strftime('%d %b %Y')
    old_time = appointment.time_slot.strftime('%I:%M %p')
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, instance=appointment)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.status = 'SCHEDULED'
            apt.save()
            
            # Send automated Reschedule notification to Patient and Owner
            notify_appointment_rescheduled(apt, old_date, old_time)
            messages.success(request, f"Appointment #{apt.id} successfully rescheduled to {apt.appointment_date} at {apt.time_slot.strftime('%H:%M')}.")
            referer = request.META.get('HTTP_REFERER')
            if referer and 'reschedule' not in referer:
                return redirect(referer)
            return redirect('appointment_list')
        else:
            messages.error(request, "Error rescheduling appointment. Check time slot availability or conflicts.")
    else:
        form = AppointmentBookingForm(instance=appointment)
        
    return render(request, 'hms_app/reschedule_appointment.html', {'form': form, 'appointment': appointment})


# --- Doctor Views ---

@doctor_required
def doctor_dashboard(request):
    if request.user.is_superuser and not hasattr(request.user, 'doctor_profile'):
        doctor = DoctorProfile.objects.first()
        if not doctor:
            messages.error(request, "No doctor profiles exist. Please seed data or register a doctor.")
            return redirect('receptionist_dashboard')
    else:
        doctor = get_object_or_404(DoctorProfile, user=request.user)

    today = timezone.now().date()
    assigned_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=today
    ).select_related('patient__user').order_by('appointment_date', 'time_slot')

    past_records = MedicalRecord.objects.filter(
        appointment__doctor=doctor
    ).select_related('appointment__patient__user').order_by('-created_at')[:10]

    context = {
        'doctor': doctor,
        'assigned_appointments': assigned_appointments,
        'past_records': past_records,
        'today': today,
    }
    return render(request, 'hms_app/doctor_dashboard.html', context)

@doctor_required
def create_medical_record(request, appointment_id):
    appointment = get_object_or_404(Appointment.objects.select_related('patient__user', 'doctor__user'), id=appointment_id)

    if hasattr(appointment, 'medical_record'):
        medical_record = appointment.medical_record
        is_new = False
    else:
        medical_record = None
        is_new = True

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=medical_record)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.appointment = appointment
            if is_new:
                rec.consultation_fee = appointment.doctor.consultation_fee
            rec.save()

            appointment.status = 'COMPLETED'
            appointment.save()

            # Send automated alert to Owner on completed consultation / billing
            notify_medical_record_created(rec)

            messages.success(request, f"Prescription & medical record recorded for Appointment #{appointment.id}.")
            return redirect('view_prescription', record_id=rec.id)
        else:
            messages.error(request, "Please correct the errors in the medical record form.")
    else:
        initial = {}
        if is_new:
            initial['consultation_fee'] = appointment.doctor.consultation_fee
        form = MedicalRecordForm(instance=medical_record, initial=initial)

    patient_history = MedicalRecord.objects.filter(
        appointment__patient=appointment.patient
    ).exclude(appointment=appointment).select_related('appointment__doctor__user').order_by('-created_at')

    context = {
        'appointment': appointment,
        'form': form,
        'is_new': is_new,
        'patient_history': patient_history,
    }
    return render(request, 'hms_app/create_medical_record.html', context)


# --- Patient Views ---

@patient_required
def patient_dashboard(request):
    if request.user.is_superuser and not hasattr(request.user, 'patient_profile'):
        patient = PatientProfile.objects.first()
        if not patient:
            messages.error(request, "No patient profiles exist.")
            return redirect('receptionist_dashboard')
    else:
        patient = get_object_or_404(PatientProfile, user=request.user)

    appointments = patient.appointments.select_related('doctor__user', 'doctor__department').order_by('-appointment_date', '-time_slot')
    medical_records = MedicalRecord.objects.filter(appointment__patient=patient).select_related('appointment__doctor__user', 'appointment__doctor__department').order_by('-created_at')

    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    return render(request, 'hms_app/patient_dashboard.html', context)


# --- Shared / Receipt View ---

@login_required
def view_prescription(request, record_id):
    record = get_object_or_404(
        MedicalRecord.objects.select_related(
            'appointment__patient__user',
            'appointment__doctor__user',
            'appointment__doctor__department'
        ),
        id=record_id
    )

    # Permission check: superuser, receptionist, doctor of record, or patient of record
    user = request.user
    is_staff_user = user.is_superuser or user.groups.filter(name='Receptionists').exists()
    is_record_doctor = hasattr(user, 'doctor_profile') and user.doctor_profile == record.appointment.doctor
    is_record_patient = hasattr(user, 'patient_profile') and user.patient_profile == record.appointment.patient

    if not (is_staff_user or is_record_doctor or is_record_patient):
        messages.error(request, "You are not authorized to view this prescription.")
        return redirect('dashboard_redirect')

    context = {
        'record': record,
        'appointment': record.appointment,
        'patient': record.appointment.patient,
        'doctor': record.appointment.doctor,
    }
    return render(request, 'hms_app/prescription_receipt.html', context)


# --- OTP Password Reset Views (Doctors, Patients, Receptionists - except owner) ---

def custom_password_reset(request):
    if request.method == 'POST':
        identifier = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=identifier, is_active=True).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier, is_active=True).first()

        if user and not user.is_superuser and user.email:
            otp = f"{random.randint(100000, 999999)}"
            request.session['reset_user_id'] = user.id
            request.session['reset_otp'] = otp
            request.session['otp_created_at'] = int(timezone.now().timestamp())
            request.session['reset_email'] = user.email
            request.session['otp_verified'] = False

            if send_password_reset_otp_email(user, otp):
                return redirect('password_reset_verify_otp')
            else:
                for key in ['reset_user_id', 'reset_otp', 'otp_created_at', 'reset_email', 'otp_verified']:
                    request.session.pop(key, None)
                messages.error(request, "Failed to send OTP email. Please try again later or contact support.")
                return render(request, 'hms_app/password_reset_form.html')
        elif user and user.is_superuser:
            messages.error(request, "Owner password reset must be done via secure admin console.")
            return render(request, 'hms_app/password_reset_form.html')
        else:
            messages.error(request, "No registered account found with that email or username.")
            return render(request, 'hms_app/password_reset_form.html')

    return render(request, 'hms_app/password_reset_form.html')


def password_reset_verify_otp(request):
    user_id = request.session.get('reset_user_id')
    saved_otp = request.session.get('reset_otp')
    user_email = request.session.get('reset_email', '')

    if not user_id or not saved_otp:
        messages.error(request, "Password reset session expired. Please enter your email again.")
        return redirect('password_reset')

    # Mask email for display: j***h@domain.com
    masked_email = user_email
    if '@' in user_email:
        local, domain = user_email.split('@', 1)
        if len(local) > 2:
            masked_email = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"
        else:
            masked_email = f"{local[0]}*@{domain}"

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        created_at = request.session.get('otp_created_at', 0)

        # Check 10-minute expiration
        if int(timezone.now().timestamp()) - created_at > 600:
            messages.error(request, "OTP has expired. Please click Resend OTP.")
            return render(request, 'hms_app/password_reset_verify_otp.html', {'masked_email': masked_email})

        if entered_otp == saved_otp:
            request.session['otp_verified'] = True
            return redirect('password_reset_new_password')
        else:
            messages.error(request, "Invalid 6-digit OTP code. Please check and try again.")

    return render(request, 'hms_app/password_reset_verify_otp.html', {'masked_email': masked_email})


def password_reset_resend_otp(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': False, 'message': 'Session expired'}, status=400)
        return redirect('password_reset')

    user = User.objects.filter(id=user_id, is_active=True).first()
    if not user or not user.email:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        return redirect('password_reset')

    otp_created_at = request.session.get('otp_created_at', 0)
    if int(timezone.now().timestamp()) - otp_created_at < 60:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
            return JsonResponse({'success': False, 'message': 'Please wait 60 seconds before requesting another OTP.'}, status=429)
        messages.error(request, "Please wait 60 seconds before requesting another OTP.")
        return redirect('password_reset_verify_otp')

    otp = f"{random.randint(100000, 999999)}"
    request.session['reset_otp'] = otp
    request.session['otp_created_at'] = int(timezone.now().timestamp())
    request.session['otp_verified'] = False

    send_password_reset_otp_email(user, otp)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'message': 'OTP resent successfully!'})

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect('password_reset_verify_otp')


def password_reset_new_password(request):
    user_id = request.session.get('reset_user_id')
    is_verified = request.session.get('otp_verified')

    if not user_id or not is_verified:
        messages.error(request, "Please verify your OTP first.")
        return redirect('password_reset')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            user.set_password(new_password)
            user.save()
            send_password_reset_success_email(user, new_password)
            for key in ['reset_user_id', 'reset_otp', 'otp_created_at', 'reset_email', 'otp_verified']:
                request.session.pop(key, None)
            return redirect('password_reset_complete')

    return render(request, 'hms_app/password_reset_new_password.html')


def custom_password_reset_complete(request):
    return render(request, 'hms_app/password_reset_complete.html')

