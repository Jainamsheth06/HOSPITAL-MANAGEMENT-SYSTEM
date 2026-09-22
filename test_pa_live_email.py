import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hos_project.settings')
django.setup()

from django.conf import settings
from hms_app.notifications import send_direct_email_to_user

print("Testing Email Dispatch...")
print("DEFAULT_FROM_EMAIL:", getattr(settings, 'DEFAULT_FROM_EMAIL', 'None'))

test_email = 'sheth.jainam.coder@gmail.com'
res = send_direct_email_to_user(
    recipient_email=test_email,
    subject="Diagnostic Test Live",
    text_content="This is a live diagnostic test from MEDINEXA.",
    html_content="<p>This is a <strong>live diagnostic test</strong> from MEDINEXA.</p>"
)

print(f"Result for {test_email}: {'SUCCESS ' if res else 'FAILED '}")
