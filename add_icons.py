import os
import re

base_html_path = r'd:\hos\hms_app\templates\hms_app\base.html'

with open(base_html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add FontAwesome
if 'font-awesome' not in content:
    content = content.replace(
        '<link rel="stylesheet" href="{% static \'hms_app/css/style.css\' %}?v=10.0">',
        '<link rel="stylesheet" href="{% static \'hms_app/css/style.css\' %}?v=10.0">\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'
    )

# 2. Add icons to nav items
icon_mapping = {
    '> Dashboard</a>': '><i class="fa-solid fa-gauge"></i> Dashboard</a>',
    '> Patients</a>': '><i class="fa-solid fa-users-medical"></i> Patients</a>',
    '> Appointments</a>': '><i class="fa-solid fa-calendar-check"></i> Appointments</a>',
    '> Doctors</a>': '><i class="fa-solid fa-user-doctor"></i> Doctors</a>',
    '> Register Patient</a>': '><i class="fa-solid fa-user-plus"></i> Register Patient</a>',
    '> Register Doctor</a>': '><i class="fa-solid fa-user-doctor"></i> Register Doctor</a>',
    '> Book Appt</a>': '><i class="fa-solid fa-calendar-plus"></i> Book Appt</a>',
    '> Book Appointment</a>': '><i class="fa-solid fa-calendar-plus"></i> Book Appointment</a>',
    '> Doctor Panel</a>': '><i class="fa-solid fa-stethoscope"></i> Doctor Panel</a>',
    '> My Portal</a>': '><i class="fa-solid fa-laptop-medical"></i> My Portal</a>',
    '> Logout ({{ user.username }})</a>': '><i class="fa-solid fa-right-from-bracket"></i> Logout ({{ user.username }})</a>',
    '> Register ▾</a>': '><i class="fa-solid fa-address-card"></i> Register ▾</a>',
}

for old, new in icon_mapping.items():
    content = content.replace(old, new)
    # Also replace instances with a space before the text
    content = content.replace('>' + ' ' + old[1:], new)

with open(base_html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated base.html")
