from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import user_passes_test
from hms_app.models import Appointment, DoctorProfile, PatientProfile, MedicalRecord

def owner_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='owner_login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def owner_login(request):
    # Ensure default owner account MediNEXA / MediNEXA_123 is always active
    if not User.objects.filter(username='MediNEXA', is_superuser=True).exists():
        user, _ = User.objects.get_or_create(username='MediNEXA')
        user.set_password('MediNEXA_123')
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.first_name = 'MediNEXA'
        user.last_name = 'Hospital Owner'
        user.email = 'sheth.jainam.coder@gmail.com'
        user.save()

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('owner_dashboard')
        else:
            return redirect('dashboard_redirect')
            
    has_owner = True
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome back, Hospital Owner {user.first_name or user.username}!")
                return redirect('owner_dashboard')
            else:
                messages.error(request, "Access Denied: This portal is exclusively for Hospital Owners & Super Administrators.")
        else:
            messages.error(request, "Invalid Owner username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'owner_app/owner_login.html', {
        'form': form,
        'has_owner': has_owner
    })

def owner_logout(request):
    logout(request)
    messages.info(request, "Owner logged out successfully.")
    return redirect('owner_login')

from hms_app.notifications import notify_record_deleted


@owner_required
def owner_dashboard(request):
    search_query = request.GET.get('q', '').strip()
    
    # 1. Receptionists
    receptionists = User.objects.filter(groups__name='Receptionists')
    
    # 2. Doctors with patient & appointment counts
    doctors_qs = DoctorProfile.objects.select_related('user', 'department').annotate(
        total_apts=Count('appointments', distinct=True)
    )
    if search_query:
        doctors_qs = doctors_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    doctors = list(doctors_qs)
    
    # 3. Patients with doctor assignment details
    patients_qs = PatientProfile.objects.select_related('user').prefetch_related(
        'appointments__doctor__user',
        'appointments__doctor__department'
    ).order_by('-created_at')
    
    if search_query:
        patients_qs = patients_qs.filter(
            Q(patient_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    patient_list_data = []
    assigned_count = 0
    unassigned_count = 0
    
    for p in patients_qs:
        all_apts = list(p.appointments.all().order_by('-appointment_date', '-time_slot'))
        latest_apt = all_apts[0] if all_apts else None
        
        # Unique assigned doctors
        assigned_docs = []
        seen_doc_ids = set()
        for apt in all_apts:
            if apt.doctor_id not in seen_doc_ids:
                seen_doc_ids.add(apt.doctor_id)
                assigned_docs.append(apt.doctor)
                
        if latest_apt:
            assigned_count += 1
        else:
            unassigned_count += 1
            
        patient_list_data.append({
            'patient': p,
            'latest_apt': latest_apt,
            'assigned_docs': assigned_docs,
            'total_apts': len(all_apts),
            'has_assigned_doctor': bool(latest_apt)
        })

    # 4. Appointments
    appointments = Appointment.objects.all().select_related(
        'patient__user', 'doctor__user', 'doctor__department'
    ).order_by('-appointment_date', '-time_slot')
    
    total_appointments_count = appointments.count()
    scheduled_count = Appointment.objects.filter(status='SCHEDULED').count()
    completed_count = Appointment.objects.filter(status='COMPLETED').count()

    # 5. Financials
    revenue_dict = MedicalRecord.objects.aggregate(total=Sum('total_amount'))
    total_revenue = revenue_dict['total'] if revenue_dict['total'] else 0.00
    
    # 6. Email alert recipients
    from hms_app.notifications import get_owner_emails
    owner_emails = get_owner_emails()
    
    context = {
        'receptionists': receptionists,
        'doctors': doctors,
        'patients_data': patient_list_data,
        'total_patients_count': len(patient_list_data) if search_query else PatientProfile.objects.count(),
        'assigned_count': assigned_count,
        'unassigned_count': unassigned_count,
        'appointments': appointments[:20],
        'total_appointments_count': total_appointments_count,
        'scheduled_count': scheduled_count,
        'completed_count': completed_count,
        'total_revenue': total_revenue,
        'search_query': search_query,
        'owner_emails': owner_emails,
    }
    return render(request, 'owner_app/owner_dashboard.html', context)

@owner_required
def delete_receptionist(request, user_id):
    user = get_object_or_404(User, id=user_id, groups__name='Receptionists')
    username = user.username
    user.delete()
    notify_record_deleted("Receptionist Staff", f"@{username}", request.user.username)
    messages.success(request, f"Receptionist '{username}' deleted successfully.")
    return redirect('owner_dashboard')
