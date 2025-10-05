from django.shortcuts import render, redirect
from .forms import RegistrationForm

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'register_success.html', {'name': form.cleaned_data['name']})
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})
