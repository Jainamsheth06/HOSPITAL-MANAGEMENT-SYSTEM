import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_project.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives

recipient = 'jainamsheth2006@gmail.com'
from_email = 'MediNEXA Hospital <noreply@medinexa.com>'
subject = '[MediNEXA]  Appointment Confirmed with Dr. Rajesh Patel on 20 Sep 2026'

text_body = """Dear Jainam Sheth,

Your appointment has been confirmed at MediNEXA Hospital.

• Patient ID: PAT-2026-9821
• Assigned Doctor: Dr. Rajesh Patel (Cardiologist)
• Scheduled Date: Sunday, 20 September 2026 at 09:00 PM
• Consultation Fee: ₹500.00
• Status: Confirmed

Login to your Patient Portal:
https://medinexa.pythonanywhere.com/login/

Best regards,
MediNEXA Healthcare Team
noreply@medinexa.com
"""

html_body = """
<div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #bfdbfe; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
    <div style="background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%); color: white; padding: 22px 24px;">
        <h2 style="margin: 0; font-size: 20px;"> Appointment Confirmed</h2>
        <p style="margin: 4px 0 0 0; opacity: 0.9; font-size: 13px;">MediNEXA Core Healthcare System</p>
    </div>
    <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
        <p>Dear <strong>Jainam Sheth</strong>,</p>
        <p>Your appointment has been successfully scheduled and assigned:</p>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 16px 0;">
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Patient ID:</td><td style="padding: 6px 0; font-weight: 700; color: #1d4ed8; font-family: monospace;">PAT-2026-9821</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Assigned Doctor:</td><td style="padding: 6px 0; font-weight: 700; color: #10b981;">Dr. Rajesh Patel</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Department:</td><td style="padding: 6px 0; font-weight: 600;">Cardiology & Heart Care</td></tr>
                <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding: 6px 0; color: #64748b;">Date & Time:</td><td style="padding: 6px 0; font-weight: 700; color: #0f172a;">Sunday, 20 Sep 2026 at 09:00 PM</td></tr>
                <tr><td style="padding: 6px 0; color: #64748b;">Fee:</td><td style="padding: 6px 0; font-weight: 700; color: #059669;">₹500.00</td></tr>
            </table>
        </div>
        <div style="text-align: center; margin: 24px 0;">
            <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700;">Access Patient Portal </a>
        </div>
        <p style="font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 12px; margin: 0;">
            Sent from <strong>noreply@medinexa.com</strong>
        </p>
    </div>
</div>
"""

msg = EmailMultiAlternatives(
    subject=subject,
    body=text_body,
    from_email=from_email,
    to=[recipient],
    reply_to=['noreply@medinexa.com'],
    headers={'Reply-To': 'noreply@medinexa.com', 'X-Sender': 'noreply@medinexa.com'}
)
msg.attach_alternative(html_body, 'text/html')
msg.send(fail_silently=False)
print(f" Successfully sent email from '{from_email}' to '{recipient}'!")
