import os
import re

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm, DashboardForm
from .models import User, Inventory, ReliefDistribution, ReliefRequest, Notification

# ---------------- HELPERS ----------------
def validate_name(name):
    # Check if the name contains only letters and spaces
    if not re.match(r'^[a-zA-Z\s]*$', name):
        return False  # Invalid name if it contains numbers or special characters
    return True


def sanitize_name(name):
    # Remove any invalid characters from the name (e.g., numbers, special characters)
    return re.sub(r'[^a-zA-Z\s]', '', name)


# ---------------- CONTACT NUMBER VALIDATION ----------------
def validate_contact(contact):
    # Ensure the contact number contains exactly 11 digits
    if len(contact) != 11 or not contact.isdigit():
        return False  # Invalid if not exactly 11 digits
    return True


# ---------------- REGISTER ----------------
def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            firstname = form.cleaned_data["firstname"]
            lastname = form.cleaned_data["lastname"]
            middlename = form.cleaned_data.get("middlename", "")
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            address = form.cleaned_data["address"]
            city = form.cleaned_data["city"]
            barangay = form.cleaned_data["barangay"]
            contact = form.cleaned_data["contact"]

            # Check if contact already exists
            if User.objects.filter(contact=contact).exists():
                messages.error(request, "This contact number is already registered.")
                return render(request, "register.html", {"form": form})

            # Validate contact number
            if not validate_contact(contact):
                messages.warning(request, "The contact number must be exactly 11 digits.")
                return render(request, "register.html", {"form": form})

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "This username is already taken.")
                return render(request, "register.html", {"form": form})

            # Validate names
            invalid_names = []
            for field, value in {"firstname": firstname, "lastname": lastname, "middlename": middlename}.items():
                if not validate_name(value):
                    invalid_names.append(
                        f"The {field} contains invalid characters. Only letters and spaces are allowed."
                    )

            if invalid_names:
                for message in invalid_names:
                    messages.warning(request, message)
                return render(request, "register.html", {"form": form})

            # Create user
            user = User.objects.create_user(
                username=username,
                firstname=firstname,
                lastname=lastname,
                middlename=middlename,
                password=password,
                address=address,
                city=city,
                barangay=barangay,
                contact=contact,
                role="FamilyHead"
            )

            messages.success(request, "Registration successful!")
            return redirect("register_success", user_id=user.userid)

    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})



# ---------------- REGISTER SUCCESS ----------------
def register_success_view(request, user_id):
    try:
        user = User.objects.get(userid=user_id)
        return render(request, "register_success.html", {"user": user})
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("register")


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check if the user exists by username and verify password
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # Store user session
                request.session["user"] = {
                    "userid": user.userid,
                    "role": user.role
                }

                if user.role == "Admin":
                    return redirect("admin_dashboard")
                else:
                    return redirect("dashboard", user_id=user.userid)
            else:
                return render(request, "login.html", {"error": "Invalid username or password."})
        except User.DoesNotExist:
            return render(request, "login.html", {"error": "Invalid username or password."})

    return render(request, "login.html")


# ---------------- DASHBOARD ----------------
def dashboard_view(request, user_id):
    session_user = request.session.get("user")
    if not session_user or str(session_user["userid"]) != str(user_id):
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    try:
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # User distributions
    user_distributions = ReliefDistribution.objects.filter(user=user).select_related('item')
    total_reliefs_received = user_distributions.count()
    relief_types_count = user_distributions.values_list('item__category', flat=True).distinct().count()
    
    # Get user's relief requests
    user_requests = ReliefRequest.objects.filter(user=user).order_by('-request_date')
    pending_request = user_requests.filter(status='pending').first()
    latest_request = user_requests.first()

    if request.method == "POST":
        form = DashboardForm(request.POST)
        if form.is_valid():
            # Update user info
            user.address = form.cleaned_data["address"]
            user.city = form.cleaned_data["city"]
            user.barangay = form.cleaned_data["barangay"]
            user.contact = form.cleaned_data["contact"]
            user.save()
            messages.success(request, "Profile updated.")
            return redirect("dashboard", user_id=user_id)
    else:
        form = DashboardForm(initial={
            "address": user.address,
            "city": user.city,
            "barangay": user.barangay,
            "contact": user.contact,
        })

    return render(request, "dashboard.html", {
        "user": user,
        "form": form,
        "user_id": user_id,
        "user_distributions": user_distributions,
        "total_reliefs_received": total_reliefs_received,
        "relief_types_count": relief_types_count,
        "user_requests": user_requests,
        "pending_request": pending_request,
        "latest_request": latest_request,
    })



# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect("login")


# ---------------- ADMIN LOGIN ----------------
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Admin login check using Django's authentication
        try:
            user = User.objects.get(username=username, role="Admin")
            if user.check_password(password):
                # Use Django's login system
                from django.contrib.auth import login
                login(request, user)
                request.session["user"] = {
                    "userid": user.userid,
                    "role": user.role
                }
                return redirect("admin_dashboard")
            else:
                return render(request, "admin_login_new.html", {"error": "Invalid credentials"})
        except User.DoesNotExist:
            return render(request, "admin_login_new.html", {"error": "Invalid credentials"})

    return render(request, "admin_login_new.html")


# ---------------- INVENTORY ----------------
def inventory_view(request):
    session_user = request.session.get("user")

    if not session_user:
        return redirect("login")

    if session_user["role"] != "Admin":
        messages.error(request, "Admins only.")
        return redirect("dashboard", user_id=session_user["userid"])

    if request.method == "POST":
        item_name = request.POST.get("item_name")
        category = request.POST.get("category")
        quantity = request.POST.get("quantity")

        if item_name and category and quantity:
            item, created = Inventory.objects.get_or_create(
                name=item_name,
                category=category,
                defaults={"quantity": int(quantity)}
            )
            if not created:
                item.quantity = int(quantity)
                item.save()

            messages.success(request, f"{item_name} saved.")

    return render(request, "inventory.html", {"inventory": Inventory.objects.all()})


# ---------------- VIEW ONLY DASHBOARD ----------------
def view_only_dashboard(request, user_id):
    # Ensure user data is fetched properly
    try:
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")
    
    # Get user's distributions
    distributions = ReliefDistribution.objects.filter(user=user).select_related('item')
    
    # Calculate statistics
    total_reliefs = distributions.count()
    relief_types = distributions.values_list('item__category', flat=True).distinct().count()
    
    return render(request, "view_only_dashboard.html", {
        "user": user, 
        "user_id": user_id,
        "distributions": distributions,
        "total_reliefs": total_reliefs,
        "relief_types": relief_types
    })


# ---------------- ADMIN STATIC PAGES ----------------
def admin_inventory(request):
    return render(request, "admin_inventory.html")

def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

def admin_relief_history(request):
    distributions = ReliefDistribution.objects.select_related('user', 'item').all()
    return render(request, "admin_relief_history.html", {"distributions": distributions})

# Custom Admin Dashboard View
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json

@login_required
def custom_admin_dashboard(request):
    # Only allow admin users
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        # Check if this is a Django admin user
        if not request.user.is_staff:
            return redirect('login')
    
    # Handle search
    search_query = request.GET.get('search', '')
    
    # Get statistics
    total_families = User.objects.filter(role='FamilyHead').count()
    total_inventory = Inventory.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_distributions = ReliefDistribution.objects.count()
    
    # Pending requests: count actual relief requests with pending status
    pending_requests = ReliefRequest.objects.filter(status='pending').count()
    
    # Get recent users with search
    recent_users = User.objects.filter(role='FamilyHead')
    if search_query:
        recent_users = recent_users.filter(
            Q(username__icontains=search_query) |
            Q(firstname__icontains=search_query) |
            Q(lastname__icontains=search_query) |
            Q(contact__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    recent_users = recent_users.order_by('-userid')[:10]
    
    # Get unread notifications count
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Get all family heads for display
    all_families = User.objects.filter(role='FamilyHead').order_by('-userid')
    
    context = {
        'admin_user': request.user,
        'total_families': total_families,
        'total_inventory': total_inventory,
        'total_distributions': total_distributions,
        'pending_requests': pending_requests,
        'recent_users': recent_users,
        'all_families': all_families,
        'unread_notifications': unread_notifications,
        'search_query': search_query,
    }
    
    return render(request, 'admin_dashboard_new.html', context)


# ---------------- MANAGE USERS ----------------
@login_required
def manage_users_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    search_query = request.GET.get('search', '')
    city_filter = request.GET.get('city', '')
    barangay_filter = request.GET.get('barangay', '')
    
    users = User.objects.filter(role='FamilyHead')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(firstname__icontains=search_query) |
            Q(lastname__icontains=search_query) |
            Q(contact__icontains=search_query)
        )
    
    if city_filter:
        users = users.filter(city__iexact=city_filter)
    
    if barangay_filter:
        users = users.filter(barangay__iexact=barangay_filter)
    
    # Optimize query with prefetch_related to avoid N+1 problem
    users = users.prefetch_related('distributions__item', 'distributions__distributed_by').order_by('-userid')
    
    # Get distinct cities and barangays for dropdowns (case-insensitive)
    all_cities = User.objects.filter(role='FamilyHead').exclude(city__isnull=True).exclude(city__exact='').values_list('city', flat=True).distinct()
    all_barangays = User.objects.filter(role='FamilyHead').exclude(barangay__isnull=True).exclude(barangay__exact='').values_list('barangay', flat=True).distinct()
    
    # Normalize cities and barangays to title case for display
    cities = sorted(set([city.strip().title() for city in all_cities if city and city.strip()]))
    barangays = sorted(set([barangay.strip().title() for barangay in all_barangays if barangay and barangay.strip()]))
    
    # Attach distribution data directly to each user object
    for user in users:
        distributions = user.distributions.all()  # Already prefetched, no extra query
        user.has_distributions = len(distributions) > 0
        user.distribution_count = len(distributions)
        user.all_distributions = list(distributions)
    
    context = {
        'users': users,
        'search_query': search_query,
        'city_filter': city_filter,
        'barangay_filter': barangay_filter,
        'cities': cities,
        'barangays': barangays,
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_manage_users.html', context)


# ---------------- UPDATE USER ----------------
@login_required
def update_user_view(request, user_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('manage_users')
    
    if request.method == "POST":
        user.firstname = request.POST.get('firstname')
        user.lastname = request.POST.get('lastname')
        user.middlename = request.POST.get('middlename', '')
        user.address = request.POST.get('address')
        user.contact = request.POST.get('contact')
        user.save()
        messages.success(request, "User updated successfully.")
        return redirect('manage_users')
    
    return render(request, 'admin_update_user.html', {'user': user})


# ---------------- DELETE USER ----------------
@login_required
def delete_user_view(request, user_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        user = User.objects.get(userid=user_id)
        user.delete()
        messages.success(request, "User deleted successfully.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('manage_users')


# ---------------- MARK AS DISTRIBUTED ----------------
@login_required
def mark_distributed_view(request, user_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        user = User.objects.get(userid=user_id)
        # Get available inventory items
        inventory_items = Inventory.objects.filter(quantity__gt=0)
        
        if request.method == "POST":
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 1))
            notes = request.POST.get('notes', '')
            
            item = Inventory.objects.get(id=item_id)
            
            if item.quantity >= quantity:
                # Create distribution record
                ReliefDistribution.objects.create(
                    user=user,
                    item=item,
                    quantity_distributed=quantity,
                    distributed_by=request.user,
                    notes=notes
                )
                
                # Update inventory
                item.quantity -= quantity
                item.save()
                
                messages.success(request, f"Distribution recorded for {user.firstname} {user.lastname}")
                return redirect('manage_users')
            else:
                messages.error(request, "Insufficient inventory quantity.")
        
        context = {
            'user': user,
            'inventory_items': inventory_items,
        }
        return render(request, 'admin_mark_distributed.html', context)
    
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('manage_users')


# ---------------- MANAGE INVENTORY ----------------
@login_required
def manage_inventory_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    if request.method == "POST":
        item_name = request.POST.get('item_name')
        category = request.POST.get('category')
        quantity = request.POST.get('quantity')
        
        if item_name and category and quantity:
            item, created = Inventory.objects.get_or_create(
                name=item_name,
                category=category,
                defaults={'quantity': int(quantity), 'created_at': timezone.now()}
            )
            
            if not created:
                item.quantity += int(quantity)
                item.updated_at = timezone.now()
                item.save()
                messages.success(request, f"{item_name} quantity updated.")
            else:
                messages.success(request, f"{item_name} added to inventory.")
            
            return redirect('manage_inventory')
    
    inventory_items = Inventory.objects.all().order_by('category', 'name')
    categories = Inventory.CATEGORY_CHOICES
    
    context = {
        'inventory_items': inventory_items,
        'categories': categories,
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_manage_inventory.html', context)


# ---------------- UPDATE INVENTORY ----------------
@login_required
def update_inventory_view(request, item_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        item = Inventory.objects.get(id=item_id)
    except Inventory.DoesNotExist:
        messages.error(request, "Item not found.")
        return redirect('manage_inventory')
    
    if request.method == "POST":
        item.name = request.POST.get('name')
        item.category = request.POST.get('category')
        item.quantity = int(request.POST.get('quantity'))
        item.updated_at = timezone.now()
        item.save()
        messages.success(request, "Inventory item updated.")
        return redirect('manage_inventory')
    
    categories = Inventory.CATEGORY_CHOICES
    return render(request, 'admin_update_inventory.html', {'item': item, 'categories': categories})


# ---------------- DELETE INVENTORY ----------------
@login_required
def delete_inventory_view(request, item_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        item = Inventory.objects.get(id=item_id)
        item.delete()
        messages.success(request, "Inventory item deleted.")
    except Inventory.DoesNotExist:
        messages.error(request, "Item not found.")
    
    return redirect('manage_inventory')


# ---------------- VIEW DISTRIBUTIONS ----------------
@login_required
def view_distributions_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    search_query = request.GET.get('search', '')
    distributions = ReliefDistribution.objects.select_related('user', 'item', 'distributed_by').all()
    
    if search_query:
        distributions = distributions.filter(
            Q(user__username__icontains=search_query) |
            Q(user__firstname__icontains=search_query) |
            Q(user__lastname__icontains=search_query) |
            Q(item__name__icontains=search_query)
        )
    
    distributions = distributions.order_by('-distribution_date')
    
    context = {
        'distributions': distributions,
        'search_query': search_query,
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_distributions.html', context)


# ---------------- VIEW PENDING REQUESTS ----------------
@login_required
def pending_requests_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    # Get pending relief requests
    pending_requests = ReliefRequest.objects.filter(status='pending').select_related('user').order_by('-request_date')
    
    context = {
        'pending_requests': pending_requests,
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_pending_requests.html', context)


# ---------------- ANALYTICS DATA ----------------
@login_required
def analytics_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    # Get distribution statistics
    total_distributed = ReliefDistribution.objects.count()
    
    # Get pending relief requests
    total_pending = ReliefRequest.objects.filter(status='pending').count()
    
    # Get inventory count
    total_inventory = Inventory.objects.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Get category-wise distribution
    category_data = ReliefDistribution.objects.values('item__category').annotate(
        total=Count('id')
    ).order_by('item__category')
    
    context = {
        'total_distributed': total_distributed,
        'total_pending': total_pending,
        'total_inventory': total_inventory,
        'category_data': list(category_data),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_analytics.html', context)


# ---------------- REPORTS ----------------
@login_required
def reports_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    # Get new users in the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users = User.objects.filter(
        role='FamilyHead',
        userid__gte=User.objects.filter(role='FamilyHead').order_by('-userid').first().userid - 100
    ).order_by('-userid')[:20]
    
    # Get recent distributions
    recent_distributions = ReliefDistribution.objects.select_related('user', 'item').order_by('-distribution_date')[:20]
    
    # Get low stock items
    low_stock_items = Inventory.objects.filter(quantity__lte=10).order_by('quantity')
    
    context = {
        'new_users': new_users,
        'recent_distributions': recent_distributions,
        'low_stock_items': low_stock_items,
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    return render(request, 'admin_reports.html', context)


# ---------------- NOTIFICATIONS ----------------
@login_required
def notifications_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    notifications = Notification.objects.all().order_by('-created_at')[:50]
    unread_count = Notification.objects.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'admin_notifications.html', context)


# ---------------- MARK NOTIFICATION AS READ ----------------
@login_required
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})


# ---------------- GET NOTIFICATIONS (AJAX) ----------------
@login_required
def get_notifications_ajax(request):
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:10]
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse({
        'notifications': data,
        'count': Notification.objects.filter(is_read=False).count()
    })


# ---------------- CREATE RELIEF REQUEST (USER) ----------------
def create_relief_request(request, user_id):
    # Check if user is logged in via custom session
    session_user = request.session.get("user")
    if not session_user or str(session_user["userid"]) != str(user_id):
        messages.error(request, "Please log in to continue.")
        return redirect('login')
    
    try:
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')
    
    # Check if user already has a pending request
    existing_pending = ReliefRequest.objects.filter(user=user, status='pending').exists()
    if existing_pending:
        messages.warning(request, "You already have a pending relief request.")
        return redirect('dashboard', user_id=user_id)
    
    if request.method == "POST":
        relief_type = request.POST.get('relief_type', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not relief_type:
            messages.error(request, "Please select a relief type.")
            return redirect('dashboard', user_id=user_id)
        
        if not notes:
            messages.error(request, "Please provide notes for your relief request.")
            return redirect('dashboard', user_id=user_id)
        
        ReliefRequest.objects.create(
            user=user,
            relief_type=relief_type,
            notes=notes,
            status='pending'
        )
        messages.success(request, "Your relief request has been submitted successfully!")
        return redirect('dashboard', user_id=user_id)
    
    return redirect('dashboard', user_id=user_id)


# ---------------- APPROVE RELIEF REQUEST (ADMIN) ----------------
@login_required
@require_http_methods(["POST"])
def approve_request_view(request, request_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        relief_request = ReliefRequest.objects.get(id=request_id)
        relief_request.status = 'approved'
        relief_request.reviewed_by = request.user
        relief_request.reviewed_date = timezone.now()
        
        # Check if relief was marked as given
        relief_given = request.POST.get('relief_given') == 'on'
        relief_request.relief_given = relief_given
        
        relief_request.save()
        
        messages.success(request, f"Request from {relief_request.user.username} has been approved.")
    except ReliefRequest.DoesNotExist:
        messages.error(request, "Relief request not found.")
    
    return redirect('pending_requests')


# ---------------- DENY RELIEF REQUEST (ADMIN) ----------------
@login_required
@require_http_methods(["POST"])
def deny_request_view(request, request_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        relief_request = ReliefRequest.objects.get(id=request_id)
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        relief_request.status = 'denied'
        relief_request.reviewed_by = request.user
        relief_request.reviewed_date = timezone.now()
        relief_request.admin_notes = admin_notes
        relief_request.save()
        
        messages.success(request, f"Request from {relief_request.user.username} has been denied.")
    except ReliefRequest.DoesNotExist:
        messages.error(request, "Relief request not found.")
    
    return redirect('pending_requests')


# ---------------- APPROVED REQUESTS (ADMIN) ----------------
@login_required
def approved_requests_view(request):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    approved_requests = ReliefRequest.objects.filter(status='approved').order_by('-reviewed_date')
    
    context = {
        'approved_requests': approved_requests,
    }
    return render(request, 'admin_approved_requests.html', context)


# ---------------- MARK RELIEF AS GIVEN (ADMIN) ----------------
@login_required
@require_http_methods(["POST"])
def mark_relief_given_view(request, request_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        relief_request = ReliefRequest.objects.get(id=request_id)
        relief_request.relief_given = True
        relief_request.save()
        
        messages.success(request, f"Relief marked as given for {relief_request.user.username}.")
    except ReliefRequest.DoesNotExist:
        messages.error(request, "Relief request not found.")
    
    return redirect('approved_requests')


# ---------------- MARK RELIEF AS NOT GIVEN (ADMIN) ----------------
@login_required
@require_http_methods(["POST"])
def mark_relief_not_given_view(request, request_id):
    if not hasattr(request.user, 'role') or request.user.role != 'Admin':
        if not request.user.is_staff:
            return redirect('login')
    
    try:
        relief_request = ReliefRequest.objects.get(id=request_id)
        relief_request.relief_given = False
        relief_request.save()
        
        messages.success(request, f"Relief marked as not given for {relief_request.user.username}.")
    except ReliefRequest.DoesNotExist:
        messages.error(request, "Relief request not found.")
    
    return redirect('approved_requests')

