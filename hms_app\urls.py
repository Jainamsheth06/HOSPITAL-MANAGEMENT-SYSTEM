from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # OTP Password Reset URLs (Doctors, Patients, Receptionists)
    path('password-reset/', views.custom_password_reset, name='password_reset'),
    path('password-reset/verify-otp/', views.password_reset_verify_otp, name='password_reset_verify_otp'),
    path('password-reset/resend-otp/', views.password_reset_resend_otp, name='password_reset_resend_otp'),
    path('password-reset/new-password/', views.password_reset_new_password, name='password_reset_new_password'),
    path('password-reset/complete/', views.custom_password_reset_complete, name='password_reset_complete'),

    # Owner URLs have been moved to owner_app

    # Receptionist URLs
    path('receptionist/signup/', views.receptionist_register, name='receptionist_register'),
    path('receptionist/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/doctors/', views.doctor_list, name='doctor_list'),
    path('receptionist/doctors/register/', views.doctor_register, name='doctor_register'),
    path('receptionist/doctors/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),
    path('receptionist/patients/', views.patient_list, name='patient_list'),
    path('receptionist/patients/register/', views.patient_register, name='patient_register'),
    path('receptionist/patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('receptionist/patients/<int:patient_id>/delete/', views.delete_patient, name='delete_patient'),
    path('receptionist/appointments/', views.appointment_list, name='appointment_list'),
    path('receptionist/appointments/book/', views.book_appointment, name='book_appointment'),
    path('receptionist/appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('receptionist/appointments/<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('receptionist/appointments/<int:appointment_id>/delete/', views.delete_appointment, name='delete_appointment'),

    # Doctor URLs
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/<int:appointment_id>/record/', views.create_medical_record, name='create_medical_record'),

    # Patient URLs
    path('patient/', views.patient_dashboard, name='patient_dashboard'),

    # Shared Prescription & Receipt URL
    path('prescription/<int:record_id>/', views.view_prescription, name='view_prescription'),
]
