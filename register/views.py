from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, DashboardForm
from .models import Registration, Inventory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

# ================================
# REGISTER VIEW
# ================================
from .utils import upload_to_supabase

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            address = form.cleaned_data['address']
            contact = form.cleaned_data['contact']
            id_proof = request.FILES.get('id_proof')

            # Create Django user
            user = User.objects.create_user(username=username, password=password)

            # Upload to Supabase bucket
            id_proof_url = upload_to_supabase(id_proof, username)

            # Save in Registration model
            Registration.objects.create(
                username=username,
                address=address,
                contact=contact,
                id_proof_url=id_proof_url
            )

            # Automatically log in the user and redirect to dashboard
            login(request, user)
            return redirect('dashboard', user_id=user.id)
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

# ================================
# LOGIN VIEW
# ================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard', user_id=user.id)
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})

    if request.user.is_authenticated:
        return redirect('dashboard', user_id=request.user.id)

    return render(request, 'login.html')


# ================================
# DASHBOARD VIEW
# ================================
def dashboard_view(request, user_id):
    # Get the Django User object
    django_user = get_object_or_404(User, id=user_id)
    
    # Get or create the Registration object using username
    registration, created = Registration.objects.get_or_create(
        username=django_user.username,
        defaults={
            'address': '',
            'contact': '',
            'id_proof_url': ''
        }
    )

    if request.method == 'POST':
        form = DashboardForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            form.save()
            return redirect('dashboard', user_id=user_id)
    else:
        form = DashboardForm(instance=registration)

    return render(request, 'dashboard.html', {
        'form': form, 
        'user': registration,
        'django_user': django_user
    })


# ================================
# LOGOUT VIEW
# ================================
def logout_view(request):
    logout(request)
    return redirect('login')


# ================================
# INVENTORY VIEW
# ================================
def inventory_view(request):
    # Check if user is authenticated and is admin/staff
    if not request.user.is_authenticated:
        return redirect('login')
    
    if not (request.user.is_staff or request.user.is_superuser):
        # Redirect non-admin users with an error message
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard', user_id=request.user.id)
    
    # Handle POST request for adding/updating inventory items
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        category = request.POST.get('category')
        quantity = request.POST.get('quantity')
        
        if item_name and category and quantity:
            try:
                # Try to get existing item or create new one
                inventory_item, created = Inventory.objects.get_or_create(
                    name=item_name,
                    category=category,
                    defaults={'quantity': int(quantity)}
                )
                if not created:
                    # Update quantity if item already exists
                    inventory_item.quantity = int(quantity)
                    inventory_item.save()
                
                messages.success(request, f'Item "{item_name}" {"added" if created else "updated"} successfully.')
                return redirect('inventory')
            except Exception as e:
                messages.error(request, f'Error saving item: {str(e)}')
                return redirect('inventory')
    
    inventories = Inventory.objects.all()
    user_id = request.user.id if request.user.is_authenticated else 1

    return render(request, 'inventory.html', {
        'inventory': inventories,
        'user_id': user_id
    })
