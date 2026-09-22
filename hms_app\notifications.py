import os
import re
import logging
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
import json
import urllib.request

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def is_valid_working_email(email):
    """Check if recipient email is valid, non-empty, and has a legitimate domain format."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    domain = parts[1]
    if '.' not in domain or len(domain.split('.')[-1]) < 2:
        return False
    return True


def send_direct_email_to_user(recipient_email, subject, text_content, html_content=None):
    """Send direct email to user (patient, doctor, staff, or owner) via Resend API / SMTP."""
    if not recipient_email or not is_valid_working_email(recipient_email):
        logger.warning(f"Direct email skipped: invalid or missing email '{recipient_email}'. Subject: {subject}")
        return False
        
    cleaned_recipient = recipient_email.strip()
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MEDINEXA <onboarding@resend.dev>')
    full_subject = f"[MEDINEXA] {subject}"
    resend_api_key = getattr(settings, 'RESEND_API_KEY', '') or os.environ.get('RESEND_API_KEY', '')

    # 1. Try Resend Direct REST API via built-in urllib (Works 100% on PythonAnywhere proxy)
    if resend_api_key:
        try:
            resend_payload = {
                "from": from_email,
                "to": [cleaned_recipient],
                "subject": full_subject,
                "text": text_content,
            }
            if html_content:
                resend_payload["html"] = html_content
            if 'noreply@medinexa.com' in from_email:
                resend_payload["reply_to"] = "noreply@medinexa.com"

            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(resend_payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "MediNEXA-HMS/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Direct email sent via Resend REST API to {cleaned_recipient}: {subject}")
                    return True
        except Exception as e:
            logger.warning(f"Resend REST API send failed for {cleaned_recipient}: {e}. Trying standard Django SMTP...")

    # 2. Try standard Django Mail Backend
    try:
        msg = EmailMultiAlternatives(
            subject=full_subject,
            body=text_content,
            from_email=from_email,
            to=[cleaned_recipient],
            reply_to=['noreply@medinexa.com'],
            headers={
                'From': from_email,
                'Reply-To': 'noreply@medinexa.com',
                'X-Sender': 'noreply@medinexa.com',
                'Sender': 'noreply@medinexa.com',
            }
        )
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Direct email sent successfully via Django Mail to {cleaned_recipient}: {subject}")
        return True
    except Exception as e:
        logger.warning(f"Django Mail send failed for {cleaned_recipient}: {e}. Trying direct Gmail SMTP...")

    # 3. Direct Universal Delivery Fallback via App Password
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        smtp_user = "sheth.jainam.coder@gmail.com"
        smtp_pass = "piavlgmkshthjxkb"
        
        raw_msg = MIMEMultipart("alternative")
        raw_msg["Subject"] = full_subject
        raw_msg["From"] = "MEDINEXA <noreply@medinexa.com>"
        raw_msg["To"] = cleaned_recipient
        raw_msg["Reply-To"] = "noreply@medinexa.com"

        if text_content:
            raw_msg.attach(MIMEText(text_content, "plain"))
        if html_content:
            raw_msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, cleaned_recipient, raw_msg.as_string())
        server.quit()
        logger.info(f"Direct email sent successfully via Universal SMTP to {cleaned_recipient}: {subject}")
        return True
    except Exception as e:
        logger.warning(f"Universal SMTP fallback failed for {cleaned_recipient}: {e}")
        return False


def get_owner_emails():
    """Get active owner email addresses configured in settings/env or superusers."""
    owner_email = getattr(settings, 'OWNER_EMAIL', '').strip()
    emails = []
    if owner_email and is_valid_working_email(owner_email):
        emails.append(owner_email)
    return emails


def send_notification_to_owner(subject, text_content, html_content=None):
    """Send summary/audit alert directly to Hospital Owner from noreply@medinexa.com without emojis."""
    owner_emails = get_owner_emails()
    for o_email in owner_emails:
        send_direct_email_to_user(o_email, f"[Owner Alert] {subject}", text_content, html_content)
    return True


# ==============================================================================
# APPOINTMENT NOTIFICATIONS
# ==============================================================================

def send_appointment_confirmation_to_patient(appointment):
    """Send appointment schedule & doctor assign email to the PATIENT."""
    pat_email = appointment.patient.user.email
    if not pat_email:
        return
        
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    dept_name = appointment.doctor.department.name if appointment.doctor.department else "General"
    subject = f"Appointment Confirmed with Dr. {doc_name} on {appointment.appointment_date.strftime('%d %b %Y')}"
    
    text_content = f"""Dear {pat_name},

Your appointment has been scheduled successfully at MediNEXA Hospital.

--- APPOINTMENT & DOCTOR DETAILS ---
- Appointment ID: #{appointment.id}
- Assigned Doctor: Dr. {doc_name} ({appointment.doctor.specialization})
- Department: {dept_name}
- Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}
- Time Slot: {appointment.time_slot.strftime('%I:%M %p')}
- Consultation Fee: Rs. {appointment.doctor.consultation_fee}

Please arrive 10 minutes before your scheduled time.

View appointment details in your portal:
https://medinexa.pythonanywhere.com/login/

Best regards,
MediNEXA Hospital Healthcare Team
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: #1e40af; color: white; padding: 20px 24px;">
            <h2 style="margin: 0; font-size: 20px;">Appointment Confirmed</h2>
            <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Appointment #{appointment.id} with Dr. {doc_name}</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
            <p>Dear <strong>{pat_name}</strong>,</p>
            <p>Your appointment has been confirmed and assigned to Dr. {doc_name}:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Assigned Doctor:</td><td style="padding: 6px 0; font-weight: 700; color: #10b981;">Dr. {doc_name}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Department:</td><td style="padding: 6px 0; font-weight: 600;">{dept_name} ({appointment.doctor.specialization})</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Date and Time:</td><td style="padding: 6px 0; font-weight: 700; color: #0f172a;">{appointment.appointment_date.strftime('%A, %d %b %Y')} at {appointment.time_slot.strftime('%I:%M %p')}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Consultation Fee:</td><td style="padding: 6px 0; font-weight: 700; color: #059669;">Rs. {appointment.doctor.consultation_fee}</td></tr>
            </table>
            <div style="text-align: center; margin-top: 24px;">
                <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View in Patient Portal</a>
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""
    send_direct_email_to_user(pat_email, subject, text_content, html_content)


def send_appointment_alert_to_doctor(appointment):
    """Send new patient assignment alert to the DOCTOR."""
    doc_email = appointment.doctor.user.email
    if not doc_email:
        return
        
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    subject = f"New Patient Assigned: {pat_name} on {appointment.appointment_date.strftime('%d %b %Y')}"
    
    text_content = f"""Dear Dr. {doc_name},

A new patient appointment has been scheduled for you at MediNEXA Hospital.

--- PATIENT & APPOINTMENT DETAILS ---
- Patient: {pat_name} (ID: {appointment.patient.patient_id})
- Blood Group: {appointment.patient.blood_group} | Gender: {appointment.patient.get_gender_display()}
- Scheduled Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}
- Time Slot: {appointment.time_slot.strftime('%I:%M %p')}
- Reason / Symptoms: {appointment.reason or 'General Consultation'}

View patient medical history in your Doctor Portal:
https://medinexa.pythonanywhere.com/login/

Best regards,
MediNEXA Hospital
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: #10b981; color: white; padding: 20px 24px;">
            <h2 style="margin: 0; font-size: 20px;">New Patient Assigned</h2>
            <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Appointment #{appointment.id}</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
            <p>Dear <strong>Dr. {doc_name}</strong>,</p>
            <p>A new consultation has been booked with you:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Patient Name:</td><td style="padding: 6px 0; font-weight: 700; color: #0f172a;">{pat_name} ({appointment.patient.patient_id})</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Date and Time:</td><td style="padding: 6px 0; font-weight: 700; color: #0f172a;">{appointment.appointment_date.strftime('%A, %d %b %Y')} at {appointment.time_slot.strftime('%I:%M %p')}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Reason / Symptoms:</td><td style="padding: 6px 0; color: #0f172a;">{appointment.reason or 'General Consultation'}</td></tr>
            </table>
            <div style="text-align: center; margin-top: 24px;">
                <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Open Doctor Portal</a>
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""
    send_direct_email_to_user(doc_email, subject, text_content, html_content)


def notify_appointment_booked(appointment):
    """Triggered when appointment is booked: Notifies PATIENT, DOCTOR, and OWNER."""
    send_appointment_confirmation_to_patient(appointment)
    send_appointment_alert_to_doctor(appointment)
    
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    subject = f"New Appointment #{appointment.id}: {pat_name} with Dr. {doc_name}"
    text = f"""Hospital Owner Alert:
A new appointment has been booked.

- Appointment ID: #{appointment.id}
- Patient: {pat_name} (ID: {appointment.patient.patient_id})
- Doctor: Dr. {doc_name} ({appointment.doctor.specialization})
- Date & Time: {appointment.appointment_date} at {appointment.time_slot}
- Fee: Rs. {appointment.doctor.consultation_fee}
"""
    send_notification_to_owner(subject, text)


def send_appointment_reschedule_to_patient(appointment, old_date=None, old_time=None):
    """Send reschedule email to the PATIENT."""
    pat_email = appointment.patient.user.email
    if not pat_email:
        return
        
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    subject = f"Appointment #{appointment.id} Rescheduled to {appointment.appointment_date.strftime('%d %b %Y')}"
    
    old_info = f" (Previous Slot: {old_date} at {old_time})" if old_date and old_time else ""
    
    text_content = f"""Dear {pat_name},

Your appointment at MediNEXA Hospital has been successfully RESCHEDULED.

--- UPDATED APPOINTMENT DETAILS ---
- Appointment ID: #{appointment.id}
- Doctor: Dr. {doc_name} ({appointment.doctor.specialization})
- NEW Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}
- NEW Time: {appointment.time_slot.strftime('%I:%M %p')}{old_info}

Please arrive 10 minutes prior to your new time slot.

View updated appointment in your portal:
https://medinexa.pythonanywhere.com/login/

Best regards,
MediNEXA Hospital
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #bfdbfe; border-radius: 12px; overflow: hidden;">
        <div style="background: #2563eb; color: white; padding: 20px 24px;">
            <h2 style="margin: 0; font-size: 20px;">Appointment Rescheduled</h2>
            <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Appointment #{appointment.id}</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
            <p>Dear <strong>{pat_name}</strong>,</p>
            <p>Your appointment schedule has been updated:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Attending Doctor:</td><td style="padding: 6px 0; font-weight: 700; color: #10b981;">Dr. {doc_name}</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">NEW Date and Time:</td><td style="padding: 6px 0; font-weight: 700; color: #2563eb;">{appointment.appointment_date.strftime('%A, %d %b %Y')} at {appointment.time_slot.strftime('%I:%M %p')}</td></tr>
            </table>
            <div style="text-align: center; margin-top: 24px;">
                <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">View In Patient Portal</a>
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""
    send_direct_email_to_user(pat_email, subject, text_content, html_content)


def send_appointment_reschedule_to_doctor(appointment, old_date=None, old_time=None):
    """Send reschedule email to the DOCTOR."""
    doc_email = appointment.doctor.user.email
    if not doc_email:
        return
        
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    subject = f"Appointment Rescheduled: {pat_name} moved to {appointment.appointment_date.strftime('%d %b %Y')}"
    
    text_content = f"""Dear Dr. {doc_name},

An appointment with patient {pat_name} (ID: {appointment.patient.patient_id}) has been rescheduled.

- NEW Date and Time: {appointment.appointment_date.strftime('%A, %d %B %Y')} at {appointment.time_slot.strftime('%I:%M %p')}
- Previous Slot: {old_date} at {old_time}

View in Doctor Portal: https://medinexa.pythonanywhere.com/login/
"""
    send_direct_email_to_user(doc_email, subject, text_content)


def notify_appointment_rescheduled(appointment, old_date=None, old_time=None):
    """Triggered when appointment is rescheduled: Notifies PATIENT, DOCTOR, and OWNER."""
    send_appointment_reschedule_to_patient(appointment, old_date, old_time)
    send_appointment_reschedule_to_doctor(appointment, old_date, old_time)
    
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    subject = f"Appointment #{appointment.id} Rescheduled: {pat_name} with Dr. {doc_name}"
    text = f"""Hospital Owner Alert:
Appointment #{appointment.id} was rescheduled.
- Patient: {pat_name} ({appointment.patient.patient_id})
- Doctor: Dr. {doc_name}
- NEW Date & Time: {appointment.appointment_date} at {appointment.time_slot}
"""
    send_notification_to_owner(subject, text)


def send_appointment_cancellation_to_patient(appointment):
    """Send appointment cancellation notice to the PATIENT."""
    pat_email = appointment.patient.user.email
    if not pat_email:
        return
        
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    subject = f"Appointment #{appointment.id} Cancelled - MediNEXA Hospital"
    
    text_content = f"""Dear {pat_name},

Your scheduled appointment with Dr. {doc_name} on {appointment.appointment_date.strftime('%d %B %Y')} at {appointment.time_slot.strftime('%I:%M %p')} has been CANCELLED.

If you would like to reschedule with another doctor, please log in to your patient portal:
https://medinexa.pythonanywhere.com/login/

Best regards,
MediNEXA Hospital
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #fee2e2; border-radius: 12px; overflow: hidden;">
        <div style="background: #ef4444; color: white; padding: 20px 24px;">
            <h2 style="margin: 0; font-size: 20px;">Appointment Cancelled</h2>
            <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 14px;">Appointment #{appointment.id}</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
            <p>Dear <strong>{pat_name}</strong>,</p>
            <p>Your appointment has been cancelled:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Doctor:</td><td style="padding: 6px 0; font-weight: 600;">Dr. {doc_name} ({appointment.doctor.specialization})</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Date and Time:</td><td style="padding: 6px 0; font-weight: 600; color: #ef4444;">{appointment.appointment_date.strftime('%d %B %Y')} at {appointment.time_slot.strftime('%I:%M %p')}</td></tr>
            </table>
            <div style="text-align: center; margin-top: 24px;">
                <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Reschedule in Patient Portal</a>
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""
    send_direct_email_to_user(pat_email, subject, text_content, html_content)


def send_appointment_cancellation_to_doctor(appointment):
    """Send appointment cancellation notice to the DOCTOR."""
    doc_email = appointment.doctor.user.email
    if not doc_email:
        return
        
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    subject = f"Appointment Cancelled: {pat_name} on {appointment.appointment_date.strftime('%d %b %Y')}"
    
    text_content = f"""Dear Dr. {doc_name},

An appointment with patient {pat_name} (ID: {appointment.patient.patient_id}) scheduled for {appointment.appointment_date} at {appointment.time_slot} has been CANCELLED.

Doctor Portal: https://medinexa.pythonanywhere.com/login/
"""
    send_direct_email_to_user(doc_email, subject, text_content)


def notify_appointment_cancelled(appointment):
    """Triggered when appointment is cancelled: Notifies PATIENT, DOCTOR, and OWNER."""
    send_appointment_cancellation_to_patient(appointment)
    send_appointment_cancellation_to_doctor(appointment)
    
    pat_name = appointment.patient.user.get_full_name() or appointment.patient.user.username
    doc_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    subject = f"Appointment #{appointment.id} Cancelled: {pat_name}"
    text = f"""Hospital Owner Alert:
Appointment #{appointment.id} with Dr. {doc_name} for patient {pat_name} ({appointment.patient.patient_id}) was cancelled.
"""
    send_notification_to_owner(subject, text)


# ==============================================================================
# USER REGISTRATION NOTIFICATIONS (DOCTOR, PATIENT, STAFF)
# Registration email goes ONLY to the registered user.
# Owner gets a notification alert about the registration WITHOUT password.
# ==============================================================================

def notify_doctor_registered(doctor, raw_password=None):
    """Send account details to newly registered DOCTOR only, and alert to OWNER without password."""
    doc_email = doctor.user.email
    full_name = f"{doctor.user.first_name} {doctor.user.last_name}".strip() or doctor.user.get_full_name().strip() or doctor.user.username
    doc_display_name = f"Dr. {full_name}" if not full_name.startswith("Dr.") else full_name
    dept_name = doctor.department.name if doctor.department else "General"
    
    # 1. Send Account Details ONLY to Doctor's registered email
    if doc_email:
        subject = f"Welcome {doc_display_name}! Your Doctor Account Details"
        
        text_content = f"""Dear {doc_display_name},

Welcome to the MediNEXA Healthcare Team! Your doctor profile has been created.

--- YOUR DOCTOR ACCOUNT DETAILS ---
- Doctor Name: {doc_display_name}
---- Username: {doctor.user.username}
{f"=== Password: {raw_password}" if raw_password else ""}
- Specialization: {doctor.specialization} ({dept_name})
- Consultation Fee: Rs. {doctor.consultation_fee}

You can log in to your Doctor Portal at:
https://medinexa.pythonanywhere.com/login/

If you ever need to reset your password, you can use our secure OTP Password Reset at:
https://medinexa.pythonanywhere.com/password-reset/

Best regards,
MediNEXA Hospital Administration
noreply@medinexa.com
"""

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #059669 0%, #0d9488 100%); color: white; padding: 22px 24px; text-align: center;">
                <h2 style="margin: 0; font-size: 22px;">Welcome {doc_display_name}</h2>
                <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">Your Official Doctor Profile</p>
            </div>
            <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
                <p>Dear <strong>{doc_display_name}</strong>,</p>
                <p>Your doctor account has been successfully registered on MediNEXA HMS:</p>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 18px; margin: 16px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr style="border-bottom: 1px solid #dcfce7;"><td style="padding: 7px 0; color: #166534; font-weight:600;">Doctor Name:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a;">{doc_display_name}</td></tr>
                        <tr style="border-bottom: 1px solid #dcfce7;"><td style="padding: 7px 0; color: #166534; font-weight:600;">Username:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{doctor.user.username}</td></tr>
                        {f'<tr style="border-bottom: 1px solid #dcfce7;"><td style="padding: 7px 0; color: #166534; font-weight:600;">Password:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{raw_password}</td></tr>' if raw_password else ''}
                        <tr style="border-bottom: 1px solid #dcfce7;"><td style="padding: 7px 0; color: #166534; font-weight:600;">Specialization:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;">{doctor.specialization} ({dept_name})</td></tr>
                        <tr><td style="padding: 7px 0; color: #166534; font-weight:600;">Consultation Fee:</td><td style="padding: 7px 0; font-weight: 700; color: #059669;">Rs. {doctor.consultation_fee}</td></tr>
                    </table>
                </div>
                <div style="text-align: center; margin-top: 24px;">
                    <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #059669; color: white; padding: 12px 26px; border-radius: 8px; text-decoration: none; font-weight: 700;">Access Doctor Portal</a>
                </div>
                <div style="margin-top: 20px; font-size: 13px; color: #64748b; text-align: center;">
                    Need to change or set your password? <a href="https://medinexa.pythonanywhere.com/password-reset/" style="color: #059669; font-weight: 600;">Use OTP Password Reset</a>
                </div>
            </div>
            <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
                Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
            </div>
        </div>"""
        send_direct_email_to_user(doc_email, subject, text_content, html_content)

    # 2. Send Summary Details to Hospital Owner (strictly NO password)
    owner_subj = f"New Doctor Registered: {doc_display_name} ({dept_name})"
    owner_text = f"""Hospital Owner Summary:
A new doctor has registered in the hospital system.

- Doctor Name: {doc_display_name}
- Username: {doctor.user.username}
- Email: {doc_email or 'N/A'}
- Specialization: {doctor.specialization}
- Department: {dept_name}
- Consultation Fee: Rs. {doctor.consultation_fee}
- Registered At: {timezone.now().strftime('%d %b %Y, %I:%M %p')}
"""
    send_notification_to_owner(owner_subj, owner_text)


def notify_patient_registered(patient, raw_password=None):
    """Send welcome details to newly registered PATIENT only, and summary to OWNER without password."""
    pat_email = patient.user.email
    pat_name = f"{patient.user.first_name} {patient.user.last_name}".strip() or patient.user.get_full_name().strip() or patient.user.username
    
    # 1. Send Details ONLY to Patient's registered email
    if pat_email:
        subject = f"Welcome {pat_name}! Your Patient ID is {patient.patient_id}"
        
        text_content = f"""Dear {pat_name},

Welcome to MediNEXA Hospital! Your patient registration is complete.

--- YOUR PATIENT DETAILS ---
- Patient Name: {pat_name}
- Unique Patient ID: {patient.patient_id}
---- Username: {patient.user.username}
{f"=== Password: {raw_password}" if raw_password else ""}
- Blood Group: {patient.blood_group}
- Registered Phone: {patient.phone or 'N/A'}

Please save your Patient ID ({patient.patient_id}) for booking appointments, checking doctor prescriptions, and viewing medical reports online.

Sign in to your Patient Portal:
https://medinexa.pythonanywhere.com/login/

If you need to reset your password, you can use our secure OTP Password Reset at:
https://medinexa.pythonanywhere.com/password-reset/

Best regards,
MediNEXA Healthcare Team
noreply@medinexa.com
"""

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%); color: white; padding: 22px 24px; text-align: center;">
                <h2 style="margin: 0; font-size: 22px;">Welcome to MediNEXA, {pat_name}!</h2>
                <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">Your Official Patient ID & Account Details</p>
            </div>
            <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
                <p>Dear <strong>{pat_name}</strong>,</p>
                <p>Thank you for registering with MediNEXA Hospital. Your profile has been created successfully:</p>
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 18px; border-radius: 10px; margin: 16px 0;">
                    <div style="text-align: center; margin-bottom: 14px;">
                        <span style="font-size: 12px; color: #1e40af; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">YOUR UNIQUE PATIENT ID</span>
                        <div style="font-size: 28px; font-weight: 800; color: #1d4ed8; font-family: monospace; margin-top: 4px;">{patient.patient_id}</div>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Patient Name:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a;">{pat_name}</td></tr>
                        <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Username:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{patient.user.username}</td></tr>
                        {f'<tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Password:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{raw_password}</td></tr>' if raw_password else ''}
                        <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Blood Group:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;">{patient.blood_group}</td></tr>
                        <tr><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Contact Phone:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;">{patient.phone or 'N/A'}</td></tr>
                    </table>
                </div>
                <div style="text-align: center; margin-top: 24px;">
                    <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 26px; border-radius: 8px; text-decoration: none; font-weight: 700;">Access Patient Portal</a>
                </div>
                <div style="margin-top: 20px; font-size: 13px; color: #64748b; text-align: center;">
                    Need to change or set your password? <a href="https://medinexa.pythonanywhere.com/password-reset/" style="color: #1e3a8a; font-weight: 600;">Use OTP Password Reset</a>
                </div>
            </div>
            <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
                Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
            </div>
        </div>"""
        send_direct_email_to_user(pat_email, subject, text_content, html_content)

    # 2. Send Summary Details to Hospital Owner (strictly NO password)
    owner_subj = f"New Patient Registered: {pat_name} ({patient.patient_id})"
    owner_text = f"""Hospital Owner Summary:
A new patient has registered with MediNEXA Hospital.

- Patient Name: {pat_name}
- Patient ID: {patient.patient_id}
- Username: {patient.user.username}
- Email: {pat_email or 'N/A'}
- Phone: {patient.phone or 'N/A'}
- Blood Group: {patient.blood_group}
- Gender: {patient.get_gender_display()}
- Registered At: {timezone.now().strftime('%d %b %Y, %I:%M %p')}
"""
    send_notification_to_owner(owner_subj, owner_text)


def notify_staff_registered(staff_user, raw_password=None):
    """Send welcome details to newly registered RECEPTIONIST / STAFF only, and summary to OWNER without password."""
    staff_email = staff_user.email
    staff_name = f"{staff_user.first_name} {staff_user.last_name}".strip() or staff_user.get_full_name().strip() or staff_user.username
    
    # 1. Send Details ONLY to Staff's registered email
    if staff_email:
        subject = f"Welcome {staff_name}! Your MediNEXA Staff Account Details"
        
        text_content = f"""Dear {staff_name},

Welcome to the MediNEXA Hospital Staff Team! Your receptionist staff account has been created.

--- YOUR STAFF ACCOUNT DETAILS ---
- Staff Name: {staff_name}
---- Username: {staff_user.username}
{f"=== Password: {raw_password}" if raw_password else ""}
- Role: Receptionist / Front Desk Staff

Log in to the Staff Portal at:
https://medinexa.pythonanywhere.com/login/

If you need to reset your password, you can use our secure OTP Password Reset at:
https://medinexa.pythonanywhere.com/password-reset/

Best regards,
MediNEXA Hospital Administration
noreply@medinexa.com
"""

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #fed7aa; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background: linear-gradient(135deg, #ea580c 0%, #f97316 100%); color: white; padding: 22px 24px; text-align: center;">
                <h2 style="margin: 0; font-size: 22px;">Welcome to MediNEXA Staff Team, {staff_name}!</h2>
                <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">Your Official Staff Portal Account Details</p>
            </div>
            <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
                <p>Dear <strong>{staff_name}</strong>,</p>
                <p>Your Receptionist account has been set up on MediNEXA HMS:</p>
                <div style="background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px; padding: 18px; margin: 16px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        <tr style="border-bottom: 1px solid #fed7aa;"><td style="padding: 7px 0; color: #9a3412; font-weight:600;">Staff Name:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a;">{staff_name}</td></tr>
                        <tr style="border-bottom: 1px solid #fed7aa;"><td style="padding: 7px 0; color: #9a3412; font-weight:600;">Username:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{staff_user.username}</td></tr>
                        {f'<tr style="border-bottom: 1px solid #fed7aa;"><td style="padding: 7px 0; color: #9a3412; font-weight:600;">Password:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">{raw_password}</td></tr>' if raw_password else ''}
                        <tr><td style="padding: 7px 0; color: #9a3412; font-weight:600;">Assigned Role:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;">Receptionist / Front Desk</td></tr>
                    </table>
                </div>
                <div style="text-align: center; margin-top: 24px;">
                    <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #ea580c; color: white; padding: 12px 26px; border-radius: 8px; text-decoration: none; font-weight: 700;">Sign In to Staff Portal</a>
                </div>
                <div style="margin-top: 20px; font-size: 13px; color: #64748b; text-align: center;">
                    Need to change or set your password? <a href="https://medinexa.pythonanywhere.com/password-reset/" style="color: #ea580c; font-weight: 600;">Use OTP Password Reset</a>
                </div>
            </div>
            <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
                Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
            </div>
        </div>"""
        send_direct_email_to_user(staff_email, subject, text_content, html_content)

    # 2. Send Summary Details to Hospital Owner (strictly NO password)
    owner_subj = f"New Staff Member Registered: {staff_name}"
    owner_text = f"""Hospital Owner Summary:
A new staff member (Receptionist) has been registered.

- Staff Name: {staff_name}
- Username: {staff_user.username}
- Email: {staff_email or 'N/A'}
- Role: Receptionist / Front Desk Staff
- Registered At: {timezone.now().strftime('%d %b %Y, %I:%M %p')}
"""
    send_notification_to_owner(owner_subj, owner_text)


def notify_owner_registered(owner_user, raw_password=None):
    pass

def notify_medical_record_created(record):
    pass

def notify_record_deleted(item_type, item_identifier, deleted_by="Staff/Admin"):
    """Notify owner when any doctor, patient, or appointment record is deleted."""
    subject = f"Record Deleted: {item_type} - {item_identifier}"
    text = f"""Hospital Owner Audit Alert:
A record was deleted from the hospital database.

- Record Type: {item_type}
- Identifier: {item_identifier}
- Deleted By: {deleted_by}
- Time: {timezone.now().strftime('%d %b %Y, %I:%M %p')}
"""
    send_notification_to_owner(subject, text)


# ==============================================================================
# OTP PASSWORD RESET NOTIFICATION (ONLY OTP SYSTEM)
# ==============================================================================

def send_password_reset_otp_email(user, otp):
    """Send 6-digit OTP verification code to user for password reset."""
    recipient_email = user.email
    if not recipient_email:
        return False
        
    full_name = f"{user.first_name} {user.last_name}".strip() or user.get_full_name().strip() or user.username
    subject = f"Your MediNEXA Password Reset OTP: {otp}"
    
    text_content = f"""Dear {full_name},

Your One-Time Password (OTP) for resetting your MediNEXA Hospital account password is:

{otp}

This OTP is valid for 10 minutes. Please enter this code on the verification page to set your new password.

If you did not request this OTP, please ignore this email or contact hospital administration.

Best regards,
MediNEXA Healthcare Team
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%); color: white; padding: 22px 24px; text-align: center;">
            <h2 style="margin: 0; font-size: 22px;">Password Reset OTP</h2>
            <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">MediNEXA Account Verification</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6; text-align: center;">
            <p style="text-align: left;">Dear <strong>{full_name}</strong>,</p>
            <p style="text-align: left;">Use the following One-Time Password (OTP) to reset the password for your account (<strong>@{user.username}</strong>):</p>
            
            <div style="background: #eff6ff; border: 2px dashed #3b82f6; border-radius: 12px; padding: 20px; margin: 24px auto; max-width: 320px;">
                <div style="font-size: 12px; color: #1e40af; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 6px;">YOUR 6-DIGIT OTP</div>
                <div style="font-size: 36px; font-weight: 800; color: #1d4ed8; letter-spacing: 8px; font-family: monospace;">{otp}</div>
            </div>
            
            <p style="font-size: 13px; color: #64748b; margin-top: 16px;">This OTP code is valid for <strong>10 minutes</strong>. Do not share it with anyone.</p>
            
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 20px; font-size: 12px; color: #64748b; text-align: left;">
                <strong>Security Notice:</strong> If you did not initiate this password reset, please secure your account or disregard this email.
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""

    return send_direct_email_to_user(recipient_email, subject, text_content, html_content)


def send_password_reset_notification(user, reset_url):
    """Fallback notification pointing to OTP password reset."""
    recipient_email = user.email
    if not recipient_email:
        return False
        
    full_name = f"{user.first_name} {user.last_name}".strip() or user.get_full_name().strip() or user.username
    subject = "Reset Your MediNEXA Password"
    
    text_content = f"""Dear {full_name},

We received a request to reset your password for your MediNEXA Hospital account (@{user.username}).

Please visit the password reset page to receive your verification OTP:
https://medinexa.pythonanywhere.com/password-reset/

Best regards,
MediNEXA Hospital Support Team
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; padding: 22px 24px; text-align: center;">
            <h2 style="margin: 0; font-size: 22px;">Password Reset Request</h2>
            <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">MediNEXA Healthcare Account Security</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>We received a request to reset the password for your account (<strong>@{user.username}</strong>).</p>
            <div style="text-align: center; margin: 28px 0;">
                <a href="https://medinexa.pythonanywhere.com/password-reset/" style="display: inline-block; background: #0284c7; color: white; padding: 13px 30px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px;">Reset Your Password</a>
            </div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 20px; font-size: 12px; color: #64748b;">
                <strong>Note:</strong> If you did not make this request, you can safely ignore this email.
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""

    return send_direct_email_to_user(recipient_email, subject, text_content, html_content)


def send_password_reset_success_email(user, new_password):
    """Send new password securely after successful password reset."""
    recipient_email = user.email
    if not recipient_email:
        return False
        
    full_name = f"{user.first_name} {user.last_name}".strip() or user.get_full_name().strip() or user.username
    subject = "Your MediNEXA Password Has Been Reset"
    
    text_content = f"""Dear {full_name},

Your password for your MediNEXA Hospital account (@{user.username}) has been successfully reset.

Your new password is:
{new_password}

You can now log in using your new credentials at:
https://medinexa.pythonanywhere.com/login/

If you did not request this change, please contact hospital administration immediately.

Best regards,
MediNEXA Healthcare Team
noreply@medinexa.com
"""

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 22px 24px; text-align: center;">
            <h2 style="margin: 0; font-size: 22px;">Password Reset Successful</h2>
            <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">MediNEXA Account Security</p>
        </div>
        <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6; text-align: left;">
            <p>Dear <strong>{full_name}</strong>,</p>
            <p>Your password for your account (<strong>@{user.username}</strong>) has been successfully reset.</p>
            
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px; margin: 24px auto; max-width: 320px; text-align: center;">
                <div style="font-size: 12px; color: #166534; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 6px;">YOUR NEW PASSWORD</div>
                <div style="font-size: 24px; font-weight: 800; color: #15803d; font-family: monospace;">{new_password}</div>
            </div>
            
            <div style="text-align: center; margin: 28px 0;">
                <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #059669; color: white; padding: 13px 30px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px;">Sign In Now</a>
            </div>
            
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 20px; font-size: 12px; color: #64748b;">
                <strong>Security Alert:</strong> If you did not make this change, please contact hospital administration immediately.
            </div>
        </div>
        <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
            Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
        </div>
    </div>"""

    return send_direct_email_to_user(recipient_email, subject, text_content, html_content)

def send_restricted_account_alert(email, attempted_username, attempted_name):
    subject = "Account Restricted - MediNEXA"
    text_content = f"Dear {attempted_name},\n\nYour account (@{attempted_username}) has been automatically restricted due to the use of inappropriate words during registration.\n\nBest regards,\nMediNEXA Healthcare Team"
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: #dc2626; color: white; padding: 22px 24px; text-align: center;">
            <h2 style="margin: 0;">Account Restricted</h2>
        </div>
        <div style="padding: 24px; color: #334155;">
            <p>Dear <strong>{attempted_name}</strong>,</p>
            <p>We noticed inappropriate words in your registration details (Username: <strong>{attempted_username}</strong>). As a result, your account has been automatically restricted by the system administrator.</p>
            <p>If you believe this is a mistake, please contact hospital administration.</p>
        </div>
    </div>
    """
    return send_direct_email_to_user(email, subject, text_content, html_content)
