from django import forms

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="Username")
    lastname = forms.CharField(max_length=100, required=True, label="Last Name")
    firstname = forms.CharField(max_length=100, required=True, label="First Name")
    middlename = forms.CharField(max_length=100, required=False, label="Middle Name")  # Optional middle name

    address = forms.CharField(max_length=255, required=True, label="Address")
    city = forms.CharField(max_length=100, required=True, label="City")
    barangay = forms.CharField(max_length=100, required=True, label="Barangay")
    contact = forms.CharField(max_length=50, required=True, label="Contact Number")

    password = forms.CharField(widget=forms.PasswordInput(), required=True, label="Password")

    # Custom validation for the contact field (if needed)
    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        if not contact.isdigit():
            raise forms.ValidationError("Contact must contain only numbers.")
        if len(contact) < 8:
            raise forms.ValidationError("Contact number is too short.")
        return contact


class DashboardForm(forms.Form):
    # Fields for updating user's address and contact number in the dashboard
    address = forms.CharField(max_length=255, required=True, label="Address")
    city = forms.CharField(max_length=100, required=True, label="City")
    barangay = forms.CharField(max_length=100, required=True, label="Barangay")
    contact = forms.CharField(max_length=50, required=True, label="Contact Number")

    # Custom validation for the contact field (if needed)
    def clean_contact(self):
        contact = self.cleaned_data.get('contact')
        if not contact.isdigit():
            raise forms.ValidationError("Contact must contain only numbers.")
        if len(contact) < 8:
            raise forms.ValidationError("Contact number is too short.")
        return contact
