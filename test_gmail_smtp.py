import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "sheth.jainam.coder@gmail.com"
app_password = "piavlgmkshthjxkb"

receiver_email = "jainamsheth2006@gmail.com"

msg = MIMEMultipart("alternative")
msg["Subject"] = " Welcome Jainam Sheth! Your MediNEXA Patient ID is PAT-2026-9901"
msg["From"] = "MEDINEXA <noreply@medinexa.com>"
msg["To"] = receiver_email
msg["Reply-To"] = "noreply@medinexa.com"

html = """
<div style="font-family: sans-serif; max-width: 580px; margin: auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <div style="background: linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%); color: white; padding: 22px 24px; text-align: center;">
        <h2 style="margin: 0; font-size: 22px;"> Welcome to MediNEXA, Jainam Sheth!</h2>
        <p style="margin: 6px 0 0 0; opacity: 0.95; font-size: 14px;">Your Official Patient ID & Login Credentials</p>
    </div>
    <div style="padding: 24px; color: #334155; font-size: 14px; line-height: 1.6;">
        <p>Dear <strong>Jainam Sheth</strong>,</p>
        <p>Thank you for registering with MediNEXA Hospital. Your profile has been created successfully:</p>
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 18px; border-radius: 10px; margin: 16px 0;">
            <div style="text-align: center; margin-bottom: 14px;">
                <span style="font-size: 12px; color: #1e40af; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">YOUR UNIQUE PATIENT ID</span>
                <div style="font-size: 28px; font-weight: 800; color: #1d4ed8; font-family: monospace; margin-top: 4px;">PAT-2026-9901</div>
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Patient Name:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a;">Jainam Sheth</td></tr>
                <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Username:</td><td style="padding: 7px 0; font-weight: 700; color: #0f172a; font-family: monospace;">@jainam_sheth</td></tr>
                <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Temporary Password:</td><td style="padding: 7px 0; font-weight: 700; color: #dc2626; font-family: monospace;">PatientPass@2026</td></tr>
                <tr style="border-bottom: 1px solid #bfdbfe;"><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Blood Group:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;"> O+</td></tr>
                <tr><td style="padding: 7px 0; color: #1e40af; font-weight:600;">Contact Phone:</td><td style="padding: 7px 0; font-weight: 600; color: #0f172a;"> +91 98765 43210</td></tr>
            </table>
        </div>
        <div style="text-align: center; margin-top: 24px;">
            <a href="https://medinexa.pythonanywhere.com/login/" style="display: inline-block; background: #1e3a8a; color: white; padding: 12px 26px; border-radius: 8px; text-decoration: none; font-weight: 700;">Access Patient Portal </a>
        </div>
    </div>
    <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
        Sent from <strong>MEDINEXA &lt;noreply@medinexa.com&gt;</strong>
    </div>
</div>
"""
text = "Welcome Jainam Sheth! Patient ID: PAT-2026-9901. Login: https://medinexa.pythonanywhere.com/login/"

msg.attach(MIMEText(text, "plain"))
msg.attach(MIMEText(html, "html"))

try:
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print(f" SUCCESS! Email delivered directly to {receiver_email} from MEDINEXA <noreply@medinexa.com>")
except Exception as e:
    print(f" Error: {e}")
