from .models import Standard, Customer, Answer
from django import forms
from django.forms import ModelForm


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