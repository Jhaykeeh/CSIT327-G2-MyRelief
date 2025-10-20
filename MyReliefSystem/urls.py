from django.contrib import admin
from django.urls import path
from register import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (protected)
    path('dashboard/<int:user_id>/', views.dashboard_view, name='dashboard'),

    # Update user ID proof
    path('dashboard/update_id/<int:user_id>/', views.update_id_proof, name='update_id_proof'),

    # Inventory page
    path('inventory/', views.inventory_view, name='inventory'),

    # Home redirects to login
    path('', views.login_view, name='home'),
]

# For handling media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
