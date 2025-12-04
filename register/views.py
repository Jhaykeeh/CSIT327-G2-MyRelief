import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import RegistrationForm, DashboardForm
from .models import Inventory, Login, AdminLogin
import re

# ---------------- SUPABASE CLIENT ----------------
try:
    from supabase import create_client

    SUPABASE_URL = getattr(settings, "SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    SUPABASE_KEY = getattr(settings, "SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None


def _supabase():
    if supabase is None:
        raise RuntimeError("Supabase is not configured.")
    return supabase


# ---------------- HELPERS ----------------
def _get_user_by_contact(contact):
    sb = _supabase()
    resp = sb.table("users").select("*").eq("contact", contact).limit(1).execute()
    return resp.data[0] if resp.data else None


def _get_user_by_username(username):
    sb = _supabase()
    resp = sb.table("users").select("*").eq("username", username).limit(1).execute()  # Query by username
    return resp.data[0] if resp.data else None


def _get_user_by_id(userid):
    sb = _supabase()
    resp = sb.table("users").select("*").eq("userid", userid).limit(1).execute()
    return resp.data[0] if resp.data else None


def _insert_user(payload):
    sb = _supabase()
    resp = sb.table("users").insert(payload).execute()
    return resp.data[0] if resp.data else None


def _update_user(userid, payload):
    sb = _supabase()
    resp = sb.table("users").update(payload).eq("userid", userid).execute()
    return resp.data[0] if resp.data else None


# ---------------- NAME VALIDATION ----------------

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
            middlename = form.cleaned_data["middlename"]
            password = form.cleaned_data["password"]
            address = form.cleaned_data["address"]
            contact = form.cleaned_data["contact"]
            username = form.cleaned_data["username"]

            # Check if contact already exists
            if _get_user_by_contact(contact):
                messages.error(request, "This contact number is already registered.")
                return render(request, "register.html", {"form": form})

            # Validate contact number
            if not validate_contact(contact):
                messages.warning(request, "The contact number must be exactly 11 digits.")
                return render(request, "register.html", {"form": form})

            # Check if username already exists
            if _get_user_by_username(username):
                messages.error(request, "This username is already taken.")
                return render(request, "register.html", {"form": form})

            # Validate names
            invalid_names = []
            for field, value in {"firstname": firstname, "lastname": lastname, "middlename": middlename}.items():
                if not validate_name(value):
                    invalid_names.append(
                        f"The {field} contains invalid characters. Only letters and spaces are allowed.")
                else:
                    # Sanitize the name (remove non-alphabetic characters)
                    value = sanitize_name(value)

            if invalid_names:
                for message in invalid_names:
                    messages.warning(request, message)
                return render(request, "register.html", {"form": form})

            payload = {
                "firstname": firstname,
                "lastname": lastname,
                "middlename": middlename,
                "password": password,
                "address": address,
                "contact": contact,
                "username": username,  # Add username to payload
                "role": "FamilyHead",
            }

            created = _insert_user(payload)
            if not created:
                messages.error(request, "Registration failed.")
                return render(request, "register.html", {"form": form})

            return redirect("register_success", user_id=created["userid"])  # Ensure we pass integer user_id

    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})


# ---------------- REGISTER SUCCESS ----------------
def register_success_view(request, user_id):
    user = _get_user_by_id(user_id)  # Ensure user_id is treated as integer
    return render(request, "register_success.html", {"user": user})


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check if the user exists by username
        user = _get_user_by_username(username)

        if not user or user.get("password") != password:
            return render(request, "login.html", {"error": "Invalid username or password."})

        # Store user session
        request.session["user"] = {
            "userid": user["userid"],
            "role": user["role"]
        }

        return redirect("dashboard", user_id=user["userid"])

    return render(request, "login.html")


# ---------------- DASHBOARD ----------------

def dashboard_view(request, user_id):
    # Retrieve the user from session
    session_user = request.session.get("user")

    # If the user is not authenticated or the user_id doesn't match session user_id, redirect to login
    if not session_user or str(session_user["userid"]) != str(user_id):
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    # Get user details by user_id
    user = _get_user_by_id(user_id)
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")

    # Process form submission
    if request.method == "POST":
        form = DashboardForm(request.POST)
        if form.is_valid():
            # Update user details
            _update_user(user_id, {
                "address": form.cleaned_data["address"],
                "contact": form.cleaned_data["contact"],
            })
            messages.success(request, "Profile updated.")
            return redirect("dashboard", user_id=user_id)
    else:
        # If it's GET request, display the form with initial values
        form = DashboardForm(initial={
            "address": user.get("address", ""),  # Ensure 'address' exists
            "contact": user.get("contact", ""),  # Ensure 'contact' exists
        })

    # Pass user data and form to the template
    return render(request, "dashboard.html", {"user": user, "form": form, "user_id": user_id})


# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect("login")


# ---------------- ADMIN LOGIN ----------------
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Admin login check (use your admin credentials or logic here)
        if username == "admin" and password == "adminpassword":  # Adjust logic as needed
            # Set admin session
            request.session["user"] = {
                "userid": 0,
                "role": "Admin"
            }
            return render(request, "admin_dashboard.html")  # Redirect to admin dashboard
        else:
            return render(request, "admin_login.html", {"error": "Invalid credentials"})

    return render(request, "admin_login.html")


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

    return render(request, "admin_inventory.html", {"inventory": Inventory.objects.all()})


# ---------------- VIEW ONLY DASHBOARD ----------------
def view_only_dashboard(request, user_id):
    # Ensure user data is fetched properly
    user = _get_user_by_id(user_id)
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "view_only_dashboard.html", {"user": user, "user_id": user_id})


# ---------------- ADMIN STATIC PAGES ----------------
def admin_inventory(request):
    return render(request, "admin_inventory.html")
