from django.contrib import admin
from django.urls import path
from register import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Custom admin panel
    path('admin-panel/dashboard/', views.custom_admin_dashboard, name='admin_dashboard'),
    
    # Manage Users
    path('admin-panel/users/', views.manage_users_view, name='manage_users'),
    path('admin-panel/users/update/<int:user_id>/', views.update_user_view, name='update_user'),
    path('admin-panel/users/delete/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('admin-panel/users/distribute/<int:user_id>/', views.mark_distributed_view, name='mark_distributed'),
    
    # Manage Inventory
    path('admin-panel/inventory/', views.manage_inventory_view, name='manage_inventory'),
    path('admin-panel/inventory/update/<int:item_id>/', views.update_inventory_view, name='update_inventory'),
    path('admin-panel/inventory/delete/<int:item_id>/', views.delete_inventory_view, name='delete_inventory'),
    
    # Distributions
    path('admin-panel/distributions/', views.view_distributions_view, name='view_distributions'),
    
    # Pending Requests
    path('admin-panel/pending/', views.pending_requests_view, name='pending_requests'),
    path('admin-panel/requests/approve/<int:request_id>/', views.approve_request_view, name='approve_request'),
    path('admin-panel/requests/deny/<int:request_id>/', views.deny_request_view, name='deny_request'),
    
    # Approved Requests
    path('admin-panel/approved/', views.approved_requests_view, name='approved_requests'),
    path('admin-panel/requests/mark-given/<int:request_id>/', views.mark_relief_given_view, name='mark_relief_given'),
    path('admin-panel/requests/mark-not-given/<int:request_id>/', views.mark_relief_not_given_view, name='mark_relief_not_given'),
    
    # Relief Request (User side)
    path('relief-request/<int:user_id>/', views.create_relief_request, name='create_relief_request'),
    
    # Analytics
    path('admin-panel/analytics/', views.analytics_view, name='analytics'),
    
    # Reports
    path('admin-panel/reports/', views.reports_view, name='reports'),
    
    # Notifications
    path('admin-panel/notifications/', views.notifications_view, name='notifications'),
    path('admin-panel/notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('admin-panel/notifications/ajax/', views.get_notifications_ajax, name='get_notifications_ajax'),

    # Admin login
    path('admin-login/', views.admin_login, name='admin_login'),

    # Authentication routes
    path('register/', views.register_view, name='register'),
    path('register/success/<int:user_id>/', views.register_success_view, name='register_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (integer user_id)
    path('dashboard/<int:user_id>/', views.dashboard_view, name='dashboard'),

    # Inventory (admin required)
    path('inventory/', views.inventory_view, name='inventory'),

    # View-only dashboard
    path('view-only-dashboard/<int:user_id>/', views.view_only_dashboard, name='view_only_dashboard'),

    # Root (home) page redirecting to login page
    path('', views.login_view, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)