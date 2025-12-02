import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import RegistrationForm, DashboardForm
from .models import Inventory

# Optional utils
try:
    from .utils import upload_to_supabase, save_to_supabase_table, get_from_supabase_table
    _HAS_UTILS = True
except Exception:
    _HAS_UTILS = False

# -------------------------------
# SUPABASE CLIENT (LOCAL + RENDER READY)
# -------------------------------
try:
    from supabase import create_client

    SUPABASE_URL = getattr(settings, "SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    
    # Use SERVICE_KEY for local/server-side, ANON_KEY can be used for client if needed
    SUPABASE_KEY = getattr(
        settings, 
        "SUPABASE_SERVICE_KEY", 
        os.getenv("SUPABASE_SERVICE_KEY", "")
    )

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

except Exception:
    supabase = None

def _supabase_table():
    if supabase is None:
        raise RuntimeError("Supabase is not configured. Check SUPABASE_URL and SUPABASE_KEY.")
    return supabase

# -------------------------------
# HELPERS
# -------------------------------
def _get_user_by_username(username):
    sb = _supabase_table()
    resp = sb.table("users").select("*").eq("username", username).limit(1).execute()
    if hasattr(resp, "data") and resp.data:
        return resp.data[0]
    return None

def _insert_user_to_supabase(payload):
    sb = _supabase_table()
    resp = sb.table("users").insert(payload).execute()
    if hasattr(resp, "data") and resp.data:
        return resp.data[0]
    return None

def _update_user_in_supabase(userid, payload):
    sb = _supabase_table()
    resp = sb.table("users").update(payload).eq("userid", userid).execute()
    if hasattr(resp, "data") and resp.data:
        return resp.data[0]
    return None

# -------------------------------
# REGISTER VIEW
# -------------------------------
def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            address = form.cleaned_data.get("address", "")
            contact = form.cleaned_data.get("contact", "")
            id_proof_file = request.FILES.get("id_proof")

            if _get_user_by_username(username):
                messages.error(request, "Username already exists.")
                return render(request, "register.html", {"form": form})

            id_proof_url = None
            if id_proof_file:
                try:
                    sb = _supabase_table()
                    bucket = getattr(settings, "SUPABASE_BUCKET", "id_proof")
                    filename = f"{username}_{id_proof_file.name}"
                    file_bytes = id_proof_file.read()

                    sb.storage.from_(bucket).upload(
                        filename,
                        file_bytes,
                        file_options={"content-type": id_proof_file.content_type}
                    )

                    pub = sb.storage.from_(bucket).get_public_url(filename)
                    id_proof_url = pub.get("publicUrl") if isinstance(pub, dict) else str(pub)

                except Exception as e:
                    messages.warning(request, f"ID upload failed: {str(e)}")

            payload = {
                "username": username,
                "password": password,
                "address": address,
                "contact": contact,
                "id_proof": id_proof_url,
                "role": form.cleaned_data.get("role", "FamilyHead"),
            }

            created = _insert_user_to_supabase(payload)
            if not created:
                messages.error(request, "Registration failed.")
                return render(request, "register.html", {"form": form})

            request.session["supabase_user"] = {
                "userid": created.get("userid"),
                "username": created.get("username"),
                "role": created.get("role"),
            }

            return redirect("dashboard", user_id=created.get("userid"))

    else:
        form = RegistrationForm()

    return render(request, "register.html", {"form": form})

# -------------------------------
# REGISTER SUCCESS VIEW
# -------------------------------
def register_success_view(request, user_id):
    session_user = request.session.get("supabase_user")
    if not session_user or str(session_user.get("userid")) != str(user_id):
        messages.error(request, "Access denied.")
        return redirect("login")

    sb = _supabase_table()
    resp = sb.table("users").select("*").eq("userid", user_id).limit(1).execute()
    user_row = resp.data[0] if resp.data else None

    return render(request, "register_success.html", {
        "supabase_user": user_row or session_user,
        "user_id": user_id,
    })

# -------------------------------
# LOGIN VIEW
# -------------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = _get_user_by_username(username)
        if not user or user.get("password") != password:
            return render(request, "login.html", {"error": "Invalid username or password."})

        request.session["supabase_user"] = {
            "userid": user.get("userid"),
            "username": user.get("username"),
            "role": user.get("role"),
        }

        return redirect("dashboard", user_id=user.get("userid"))

    if request.session.get("supabase_user"):
        uid = request.session["supabase_user"]["userid"]
        return redirect("dashboard", user_id=uid)

    return render(request, "login.html")

# -------------------------------
# DASHBOARD VIEW
# -------------------------------
def dashboard_view(request, user_id):
    session_user = request.session.get("supabase_user")
    if not session_user or str(session_user.get("userid")) != str(user_id):
        messages.error(request, "Access denied.")
        return redirect("login")

    sb = _supabase_table()
    resp = sb.table("users").select("*").eq("userid", user_id).limit(1).execute()
    user_row = resp.data[0] if resp.data else None

    initial = {
        "username": user_row.get("username"),
        "address": user_row.get("address"),
        "contact": user_row.get("contact"),
        "id_proof_url": user_row.get("id_proof"),
    }

    if request.method == "POST":
        form = DashboardForm(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            address = form.cleaned_data["address"]
            contact = form.cleaned_data["contact"]
            id_proof_file = request.FILES.get("id_proof")
            id_proof_url = user_row.get("id_proof")

            if id_proof_file:
                try:
                    bucket = getattr(settings, "SUPABASE_BUCKET", "id_proof")
                    filename = f"{session_user['username']}_{id_proof_file.name}"
                    file_bytes = id_proof_file.read()

                    sb.storage.from_(bucket).upload(
                        filename,
                        file_bytes,
                        file_options={"content-type": id_proof_file.content_type}
                    )

                    pub = sb.storage.from_(bucket).get_public_url(filename)
                    id_proof_url = pub.get("publicUrl") if isinstance(pub, dict) else str(pub)

                except Exception as e:
                    messages.warning(request, f"Upload failed: {str(e)}")

            _update_user_in_supabase(user_id, {
                "address": address,
                "contact": contact,
                "id_proof": id_proof_url,
            })

            messages.success(request, "Profile updated.")
            return redirect("dashboard", user_id=user_id)

    else:
        form = DashboardForm(initial=initial)

    return render(request, "dashboard.html", {
        "form": form,
        "supabase_user": user_row,
        "user_id": user_id,
    })

# -------------------------------
# LOGOUT VIEW
# -------------------------------
def logout_view(request):
    request.session.flush()
    return redirect("login")

# -------------------------------
# INVENTORY VIEW
# -------------------------------
def inventory_view(request):
    session_user = request.session.get("supabase_user")
    if not session_user:
        return redirect("login")

    if session_user.get("role") != "Admin":
        messages.error(request, "Admin only.")
        return redirect("dashboard", user_id=session_user["userid"])

    if request.method == "POST":
        item_name = request.POST.get("item_name")
        category = request.POST.get("category")
        quantity = request.POST.get("quantity")

        if item_name and category and quantity:
            item, created = Inventory.objects.get_or_create(
                name=item_name,
                category=category,
                defaults={"quantity": int(quantity)},
            )
            if not created:
                item.quantity = int(quantity)
                item.save()

            messages.success(request, f"{item_name} saved.")

    return render(request, "inventory.html", {
        "inventory": Inventory.objects.all(),
        "user_id": session_user["userid"]
    })

# -------------------------------
# VIEW-ONLY DASHBOARD VIEW
# -------------------------------
def view_only_dashboard(request, user_id):
    session_user = request.session.get("supabase_user")
    if not session_user or str(session_user.get("userid")) != str(user_id):
        messages.error(request, "Access denied.")
        return redirect("login")

    sb = _supabase_table()
    resp = sb.table("users").select("*").eq("userid", user_id).limit(1).execute()
    user_row = resp.data[0] if resp.data else None

    return render(request, "view_only_dashboard.html", {
        "supabase_user": user_row or session_user,
        "user_id": user_id,
    })
