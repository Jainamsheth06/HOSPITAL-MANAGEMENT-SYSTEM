import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_project.settings')
django.setup()

from hms_app.notifications import send_direct_email_to_user

recipients = ['sheth.jainam.coder@gmail.com', 'jainamsheth2006@gmail.com']

subject = "Test Email from MEDINEXA"
text_content = """નમસ્તે,

આ MEDINEXA તરફથી મોકલેલો ટેસ્ટ ઈમેઇલ છે.
Sender Name: MEDINEXA <noreply@medinexa.com>

Best regards,
MEDINEXA Healthcare Team
"""

html_content = """
<div style="font-family: Arial, sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <div style="background: linear-gradient(135deg, #1e40af 0%, #0284c7 100%); color: white; padding: 22px 24px; text-align: center;">
        <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;"> MEDINEXA</h1>
        <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 14px;">Official Hospital Notification Test</p>
    </div>
    <div style="padding: 24px; color: #334155; font-size: 15px; line-height: 1.6;">
        <p>નમસ્તે,</p>
        <p>આ ઈમેઇલ સફળતાપૂર્વક <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong> દ્વારા મોકલવામાં આવ્યો છે.</p>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin: 16px 0;">
            <p style="margin: 0 0 6px 0; font-weight: bold; color: #166534;"> Sender Email Verification:</p>
            <p style="margin: 0; color: #15803d; font-family: monospace;">From: MEDINEXA &lt;noreply@medinexa.com&gt;</p>
            <p style="margin: 4px 0 0 0; color: #15803d; font-family: monospace;">Reply-To: noreply@medinexa.com</p>
        </div>
        <p style="color: #64748b; font-size: 13px;">આ મેઇલ Doctor, Patient અને Staff/Receptionist માટે ટેસ્ટિંગ તરીકે મોકલ્યો છે.</p>
    </div>
    <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px; text-align: center; color: #94a3b8; font-size: 12px;">
        © 2026 MEDINEXA Healthcare System | All Rights Reserved
    </div>
</div>
"""

for email in recipients:
    res = send_direct_email_to_user(email, subject, text_content, html_content)
    print(f"Status for {email}: {'SUCCESS ' if res else 'FAILED '}")
