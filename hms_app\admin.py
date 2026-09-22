from django.contrib import admin
from .models import Department, DoctorProfile, PatientProfile, Appointment, MedicalRecord

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'department', 'specialization', 'consultation_fee', 'phone')
    list_filter = ('department', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')

    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name() or obj.user.username}"
    get_full_name.short_description = 'Doctor Name'

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'get_full_name', 'gender', 'blood_group', 'emergency_contact', 'phone')
    search_fields = ('patient_id', 'user__username', 'user__first_name', 'user__last_name', 'phone')
    list_filter = ('gender', 'blood_group')

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Patient Name'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'time_slot', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient__patient_id', 'patient__user__first_name', 'doctor__user__first_name')

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'get_doctor', 'consultation_fee', 'medicine_fee', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('appointment__patient__patient_id', 'diagnosis')

    def get_patient(self, obj):
        return obj.appointment.patient
    get_patient.short_description = 'Patient'

    def get_doctor(self, obj):
        return obj.appointment.doctor
    get_doctor.short_description = 'Doctor'
