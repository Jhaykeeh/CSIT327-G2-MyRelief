from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, DashboardForm
from .models import Registration, Inventory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

# ================================
# REGISTER VIEW
# ================================
from .utils import upload_to_supabase, save_to_supabase_table, get_from_supabase_table

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            address = form.cleaned_data['address']
            contact = form.cleaned_data['contact']
            id_proof = request.FILES.get('id_proof')
            
            user = None
            try:
                # Create Django user
                user = User.objects.create_user(username=username, password=password)
            except Exception as e:
                # If user creation fails (e.g., username already exists)
                messages.error(request, f'Registration failed: Username "{username}" already exists or invalid.')
                return render(request, 'register.html', {'form': form})
            
            try:
                # Step 1: Upload image to Supabase storage bucket first
                id_proof_url = None
                if id_proof:
                    id_proof_url = upload_to_supabase(id_proof, username)
                    if not id_proof_url:
                        messages.warning(request, 'Registration successful, but ID proof upload failed. You can update it later.')

                # Step 2: Save all data (including image URL) to Supabase Register table
                supabase_saved = save_to_supabase_table(
                    username=username,
                    password=password,
                    address=address,
                    contact=contact,
                    id_proof_url=id_proof_url  # This will be stored in the 'id_proof' column
                )
                
                if not supabase_saved:
                    messages.warning(request, 'Registration successful locally, but Supabase save failed. Please contact support.')

                # Save in local Django Registration model (for backward compatibility)
                Registration.objects.create(
                    username=username,
                    address=address,
                    contact=contact,
                    id_proof_url=id_proof_url
                )

                # Automatically log in the user and redirect to success page
                login(request, user)
                return redirect('register_success', user_id=user.id)
            except Exception as e:
                # If something fails after user creation, delete the user and show error
                if user:
                    try:
                        User.objects.filter(id=user.id).delete()
                    except:
                        pass
                messages.error(request, f'Registration failed: {str(e)}')
                return render(request, 'register.html', {'form': form})
        else:
            # Form is invalid, display errors will be shown in template
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

# ================================
# REGISTER SUCCESS VIEW
# ================================
def register_success_view(request, user_id):
    return render(request, 'register_success.html', {'user_id': user_id})

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
    """
    Dashboard/Profile view that retrieves and displays user data from Supabase.
    """
    # Get the Django User object
    django_user = get_object_or_404(User, id=user_id)
    
    # Try to retrieve user data from Supabase first
    supabase_user_data = get_from_supabase_table(django_user.username)
    
    # Get or create local Registration object (for backward compatibility)
    registration, created = Registration.objects.get_or_create(
        username=django_user.username,
        defaults={
            'address': '',
            'contact': '',
            'id_proof_url': ''
        }
    )
    
    # If Supabase data exists, use it; otherwise use local data
    if supabase_user_data:
        # Update local model with Supabase data (for display)
        registration.username = supabase_user_data.get('username', django_user.username)
        registration.address = supabase_user_data.get('address', '')
        registration.contact = supabase_user_data.get('contact', '')
        # Note: Supabase column is 'id_proof', not 'id_proof_url'
        registration.id_proof_url = supabase_user_data.get('id_proof', '') or supabase_user_data.get('id_proof_url', '')
    
    # Handle form submission for updates
    if request.method == 'POST':
        form = DashboardForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            # Save to local database
            form.save()
            
            # TODO: Optionally update Supabase table here if you want to sync updates
            # For now, updates only go to local database
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard', user_id=user_id)
    else:
        form = DashboardForm(instance=registration)

    return render(request, 'dashboard.html', {
        'form': form, 
        'user': registration,
        'django_user': django_user,
        'supabase_data': supabase_user_data  # Pass Supabase data to template
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
