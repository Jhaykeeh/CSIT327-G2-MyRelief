from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, DashboardForm
from .models import Registration
from django.contrib.auth import logout
from .models import Inventory


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'register_success.html')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    return render(request, 'login.html')

def dashboard_view(request, user_id):
    user = get_object_or_404(Registration, id=user_id)

    if request.method == 'POST':
        form = DashboardForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('dashboard', user_id=user.id)
    else:
        form = DashboardForm(instance=user)

    return render(request, 'dashboard.html', {'form': form, 'user': user})

def update_id_proof(request, user_id):
    user = get_object_or_404(Registration, id=user_id)
    if request.method == "POST" and request.FILES.get('id_proof'):
        user.id_proof = request.FILES['id_proof']
        user.save()
    return redirect('dashboard', user_id=user.id)

def logout_view(request):
    logout(request)
    return redirect('login')


def inventory_view(request):
    inventories = Inventory.objects.all()

    # Temporary fix for missing user (since Supabase not yet connected)
    user_id = request.user.id if request.user.is_authenticated else 1  # placeholder id

    return render(request, 'inventory.html', {
        'inventories': inventories,
        'user_id': user_id
    })