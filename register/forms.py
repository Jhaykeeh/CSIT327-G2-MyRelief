from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Username")

    class Meta:
        model = Registration
        fields = ['username', 'address', 'contact', 'id_proof']

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        if not contact.isdigit():
            raise forms.ValidationError("Contact must contain only numbers.")
        if len(contact) < 8:
            raise forms.ValidationError("Contact number is too short.")
        return contact

class DashboardForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['username', 'address', 'contact', 'id_proof']
