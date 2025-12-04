from django.contrib import admin
from django.urls import path
from register import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin login
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboardSelection, name='admin_dashboardSelection'),
    path('dashboard-view/', views.admin_dashboard, name='admin_dashboard'),
    path('residents/', views.admin_residents, name='admin_residents'),

    # Authentication routes
    path('register/', views.register_view, name='register'),
    path('register/success/<int:user_id>/', views.register_success_view, name='register_success'),  # Changed to int
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (integer user_id)
    path('dashboard/<int:user_id>/', views.dashboard_view, name='dashboard'),  # Changed to int

    # Inventory (admin required)
    path('inventory/', views.inventory_view, name='inventory'),

    # View-only dashboard
    path('view-only-dashboard/<int:user_id>/', views.view_only_dashboard, name='view_only_dashboard'),  # Changed to int

    # Root (home) page redirecting to login page
    path('', views.login_view, name='home'),  # Redirects to the login page
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
