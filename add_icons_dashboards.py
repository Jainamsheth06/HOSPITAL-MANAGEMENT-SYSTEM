import os
import glob

dashboard_files = []
dashboard_files.extend(glob.glob('d:/hos/hms_app/templates/hms_app/*dashboard.html'))
dashboard_files.extend(glob.glob('d:/hos/owner_app/templates/owner_app/*dashboard.html'))

icon_mapping = {
    '> + Add Doctor': '><i class="fa-solid fa-user-doctor"></i> Add Doctor',
    '>  + Add Doctor': '><i class="fa-solid fa-user-doctor"></i> Add Doctor',
    '> + Add Patient': '><i class="fa-solid fa-user-plus"></i> Add Patient',
    '>  + Add Patient': '><i class="fa-solid fa-user-plus"></i> Add Patient',
    '> Assign Doctor': '><i class="fa-solid fa-stethoscope"></i> Assign Doctor',
    '>  Assign Doctor': '><i class="fa-solid fa-stethoscope"></i> Assign Doctor',
    '> + Add Receptionist': '><i class="fa-solid fa-user-tie"></i> Add Receptionist',
    '>  + Add Receptionist': '><i class="fa-solid fa-user-tie"></i> Add Receptionist',
    '> Register Patient': '><i class="fa-solid fa-user-plus"></i> Register Patient',
    '>  Register Patient': '><i class="fa-solid fa-user-plus"></i> Register Patient',
    '> Full Patient List': '><i class="fa-solid fa-users-medical"></i> Full Patient List',
    '>  Full Patient List': '><i class="fa-solid fa-users-medical"></i> Full Patient List',
    '> Full Doctor List': '><i class="fa-solid fa-user-doctor"></i> Full Doctor List',
    '>  Full Doctor List': '><i class="fa-solid fa-user-doctor"></i> Full Doctor List',
    '> Search doctors': '><i class="fa-solid fa-magnifying-glass"></i> Search doctors',
    '> SUPER ADMIN & OWNER PORTAL': '><i class="fa-solid fa-crown"></i> SUPER ADMIN & OWNER PORTAL',
    '> Direct Alerts Active:': '><i class="fa-solid fa-bell"></i> Direct Alerts Active:',
    '> View History': '><i class="fa-solid fa-clock-rotate-left"></i> View History',
    '>  View History': '><i class="fa-solid fa-clock-rotate-left"></i> View History',
    '> Delete': '><i class="fa-solid fa-trash"></i> Delete',
    '> Cancel': '><i class="fa-solid fa-xmark"></i> Cancel',
    '> Search': '><i class="fa-solid fa-magnifying-glass"></i> Search',
    '> Clear Filter': '><i class="fa-solid fa-filter-circle-xmark"></i> Clear Filter',
    '> History': '><i class="fa-solid fa-clock-rotate-left"></i> History',
    '>  History': '><i class="fa-solid fa-clock-rotate-left"></i> History',
    '> Book Appointment': '><i class="fa-solid fa-calendar-plus"></i> Book Appointment',
    '>  Book Appointment': '><i class="fa-solid fa-calendar-plus"></i> Book Appointment',
    # Headings
    '> Patient Registrations': '><i class="fa-solid fa-users-viewfinder"></i> Patient Registrations',
    '>  Patient Registrations': '><i class="fa-solid fa-users-viewfinder"></i> Patient Registrations',
    '> Registered Doctors': '><i class="fa-solid fa-user-md"></i> Registered Doctors',
    '>  Registered Doctors': '><i class="fa-solid fa-user-md"></i> Registered Doctors',
    '> Recent Appointments': '><i class="fa-solid fa-calendar-check"></i> Recent Appointments',
    '>  Recent Appointments': '><i class="fa-solid fa-calendar-check"></i> Recent Appointments',
    '> Receptionist Staff': '><i class="fa-solid fa-users"></i> Receptionist Staff',
    '>  Receptionist Staff': '><i class="fa-solid fa-users"></i> Receptionist Staff',
}

for file_path in dashboard_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in icon_mapping.items():
        content = content.replace(old, new)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {file_path}")
