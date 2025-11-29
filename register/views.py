from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .forms import RegistrationForm, DashboardForm
from .models import User, Inventory
import os

# Supabase client for file uploads only
try:
    from supabase import create_client

    SUPABASE_URL = getattr(settings, "SUPABASE_URL")
    SUPABASE_KEY = getattr(settings, "SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None



# REGISTER VIEW (Using ORM)
def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            address = form.cleaned_data.get("address", "")
            contact = form.cleaned_data.get("contact", "")
            id_proof_file = request.FILES.get("id_proof")

            # ORM: Check if username exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return render(request, "register.html", {"form": form})

            # Upload ID proof to Supabase Storage
            id_proof_url = None
            if id_proof_file and supabase:
                try:
                    bucket = getattr(settings, "SUPABASE_BUCKET", "id_proof")
                    filename = f"{username}_{id_proof_file.name}"
                    file_bytes = id_proof_file.read()

                    supabase.storage.from_(bucket).upload(
                        filename,
                        file_bytes,
                        file_options={"content-type": id_proof_file.content_type}
                    )

                    pub = supabase.storage.from_(bucket).get_public_url(filename)
                    id_proof_url = pub.get("publicUrl") if isinstance(pub, dict) else str(pub)

                except Exception as e:
                    messages.warning(request, f"ID upload failed: {str(e)}")

            # ORM: Create new user using Django model
            user = User(
                username=username,
                address=address,
                contact=contact,
                id_proof=id_proof_url,
                role="FamilyHead"
            )
            user.set_password(password)  # Hash password
            user.save()  # Save to database via ORM

            # Store user info in session
            request.session["user_id"] = str(user.userid)
            request.session["username"] = user.username
            request.session["role"] = user.role

            messages.success(request, "Registration successful!")
            return redirect("register_success", user_id=user.userid)

    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})



# LOGIN VIEW (Using ORM)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            # ORM: Query user from database using Django ORM
            user = User.objects.get(username=username)

            # ORM: Verify password using model method
            if user.check_password(password):
                # Login successful - store in session
                request.session["user_id"] = str(user.userid)
                request.session["username"] = user.username
                request.session["role"] = user.role

                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("dashboard", user_id=user.userid)
            else:
                messages.error(request, "Invalid username or password.")

        except User.DoesNotExist:
            # ORM: Handle user not found
            messages.error(request, "Invalid username or password.")

        return render(request, "login.html")

    # Check if already logged in
    if request.session.get("user_id"):
        return redirect("dashboard", user_id=request.session["user_id"])

    return render(request, "login.html")



# DASHBOARD VIEW (Using ORM)
def dashboard_view(request, user_id):
    # Check session authentication
    session_user_id = request.session.get("user_id")
    if not session_user_id or str(session_user_id) != str(user_id):
        messages.error(request, "Access denied. Please log in.")
        return redirect("login")

    try:
        # ORM: Get user from database
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    if request.method == "POST":
        # Handle profile updates
        address = request.POST.get("address")
        contact = request.POST.get("contact")
        id_proof_file = request.FILES.get("id_proof")

        # ORM: Update user fields
        user.address = address
        user.contact = contact

        # Upload new ID proof if provided
        if id_proof_file and supabase:
            try:
                bucket = getattr(settings, "SUPABASE_BUCKET", "id_proof")
                filename = f"{user.username}_{id_proof_file.name}"
                file_bytes = id_proof_file.read()

                supabase.storage.from_(bucket).upload(
                    filename,
                    file_bytes,
                    file_options={"content-type": id_proof_file.content_type}
                )

                pub = supabase.storage.from_(bucket).get_public_url(filename)
                user.id_proof = pub.get("publicUrl") if isinstance(pub, dict) else str(pub)

            except Exception as e:
                messages.warning(request, f"Upload failed: {str(e)}")

        # ORM: Save changes to database
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("dashboard", user_id=user_id)

    # Prepare form with current user data
    initial_data = {
        "username": user.username,
        "address": user.address,
        "contact": user.contact,
        "id_proof_url": user.id_proof,
    }
    form = DashboardForm(initial=initial_data)

    return render(request, "dashboard.html", {
        "form": form,
        "user": user,
        "supabase_user": user,  # For template compatibility
        "user_id": user_id,
    })


# REGISTER SUCCESS VIEW
def register_success_view(request, user_id):
    session_user_id = request.session.get("user_id")
    if not session_user_id or str(session_user_id) != str(user_id):
        messages.error(request, "Access denied.")
        return redirect("login")

    try:
        #ORM: Get user data
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "register_success.html", {
        "supabase_user": user,
        "user_id": user_id,
    })



# LOGOUT VIEW

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect("login")



# INVENTORY VIEW (Admin Only)
def inventory_view(request):
    session_user_id = request.session.get("user_id")
    if not session_user_id:
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    try:
        # ✅ ORM: Get user
        user = User.objects.get(userid=session_user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # Check if user is admin
    if user.role != "Admin":
        messages.error(request, "Admin access only.")
        return redirect("dashboard", user_id=user.userid)

    if request.method == "POST":
        item_name = request.POST.get("item_name")
        category = request.POST.get("category")
        quantity = request.POST.get("quantity")

        if item_name and category and quantity:
            # ORM: Get or create inventory item
            item, created = Inventory.objects.get_or_create(
                name=item_name,
                category=category,
                defaults={"quantity": int(quantity)},
            )

            if not created:
                item.quantity = int(quantity)
                item.save()

            action = "added" if created else "updated"
            messages.success(request, f"{item_name} {action} successfully.")

    # ORM: Get all inventory items
    inventory_items = Inventory.objects.all().order_by('category', 'name')

    return render(request, "inventory.html", {
        "inventory": inventory_items,
        "user_id": session_user_id
    })


# ===================================
# VIEW-ONLY DASHBOARD
# ===================================
def view_only_dashboard(request, user_id):
    session_user_id = request.session.get("user_id")
    if not session_user_id or str(session_user_id) != str(user_id):
        messages.error(request, "Access denied.")
        return redirect("login")

    try:
        # ORM: Get user
        user = User.objects.get(userid=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "view_only_dashboard.html", {
        "supabase_user": user,
        "user_id": user_id,
    })