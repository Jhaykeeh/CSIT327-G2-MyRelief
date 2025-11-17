from django.contrib import admin
from django.urls import path
from register import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
