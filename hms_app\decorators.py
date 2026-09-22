from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def receptionist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or request.user.groups.filter(name='Receptionists').exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access Denied: Only Receptionists can access this portal.")
    return _wrapped_view

def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or hasattr(request.user, 'doctor_profile') or request.user.groups.filter(name='Doctors').exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access Denied: Only Doctors can access this portal.")
    return _wrapped_view

def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or hasattr(request.user, 'patient_profile') or request.user.groups.filter(name='Patients').exists():
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Access Denied: Only Patients can access this portal.")
    return _wrapped_view
