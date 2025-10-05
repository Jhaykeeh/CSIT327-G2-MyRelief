from django import forms
from .models import Registration

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['name', 'address', 'contact', 'id_proof']

    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        if not contact.isdigit():
            raise forms.ValidationError("Contact must contain only numbers.")
        if len(contact) < 8:
            raise forms.ValidationError("Contact number is too short.")
        return contact
