from django.contrib import admin
from django.urls import path
from register import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('admin-inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-login/', views.admin_login, name='admin_login'),
    # Authentication routes
    path('register/', views.register_view, name='register'),
    path('register/success/<uuid:user_id>/', views.register_success_view, name='register_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (UUID user_id)
    path('dashboard/<uuid:user_id>/', views.dashboard_view, name='dashboard'),

    # Inventory (admin required)
    path('inventory/', views.inventory_view, name='inventory'),

    # Home → Login
    path('', views.login_view, name='home'),

    # Add the view-only dashboard URL path
    path('view-only-dashboard/<uuid:user_id>/', views.view_only_dashboard, name='view_only_dashboard'),


]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
