from django.contrib import admin
from .models import User, Inventory, ReliefDistribution, Notification

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'firstname', 'lastname', 'contact', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'firstname', 'lastname', 'contact')
    ordering = ('username',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(ReliefDistribution)
class ReliefDistributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'quantity_distributed', 'distribution_date')
    list_filter = ('distribution_date', 'item')
    search_fields = ('user__username', 'item__name')
    ordering = ('-distribution_date',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    ordering = ['-created_at']