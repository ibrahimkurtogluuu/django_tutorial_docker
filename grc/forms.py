from .models import Standard, Customer, Answer
from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)


    DISALLOWED_EMAIL_DOMAINS = [
    'example.com', 
    'test.com',
    'demo.com',
    'invalid.com',
    'fake.com',
    'spam.com',
    'testmail.com',
    'mailinator.com',
    'tempmail.com',
    'gmail.com',
    'yahoo.com',
    'hotmail.com',
    'outlook.com',
    'live.com',
    'icloud.com',
    'aol.com',
    'protonmail.com',
    'yandex.com',
    'zoho.com',
    'gmx.com',
    
    ]

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


    def clean_email(self):
        email = self.cleaned_data.get('email')
        domain = email.split('@')[1] if '@' in email else ''
        if domain in self.DISALLOWED_EMAIL_DOMAINS:
            raise forms.ValidationError("This email domain is not allowed. Please use business email.")
        return email



class StandardForm(ModelForm):
    class Meta:
        model = Standard
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            }
        labels = {
            'name': 'Standard Name',
            'description': 'Description',
}

class SubmittedAnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['response']  # Only response is editable
        widgets = {
            'response': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'response': 'Your Answer',
        }

        def clean_url(self):
            if response.question.id == 1:
                response = self.cleaned_data.get('response')
                if response:  # Only validate if response is provided
                    validator = URLValidator(schemes=['http', 'https'])  # Restrict to http/https
                    try:
                        validator(response)
                    except ValidationError:
                        raise forms.ValidationError("Please enter a valid URL (e.g., https://example.com).")
                return response