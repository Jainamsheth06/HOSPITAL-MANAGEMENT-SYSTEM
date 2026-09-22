import re
from django.core.exceptions import ValidationError

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email_address(email):
    if not email:
        raise ValidationError("Email address is required.")
    email = email.strip()
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Please enter a valid working email address (e.g. name@gmail.com).")
    parts = email.split('@')
    domain = parts[1]
    if '.' not in domain or len(domain.split('.')[-1]) < 2:
        raise ValidationError("Please enter a valid email domain (e.g. gmail.com).")
    return email.lower()

class OwnerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter strong password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter unique username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address'}),
        }

    def clean_email(self):
        return validate_email_address(self.cleaned_data.get('email'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Give them full owner privileges!
        user.is_superuser = True
        user.is_staff = True
        if commit:
            user.save()
        return user

