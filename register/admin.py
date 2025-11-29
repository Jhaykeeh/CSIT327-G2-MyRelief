from django.contrib import admin
from .models import User, Inventory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'contact', 'address', 'created_at')
    search_fields = ('username', 'contact')
    list_filter = ('role', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('userid', 'password', 'created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('userid', 'username', 'role')
        }),
        ('Contact Details', {
            'fields': ('contact', 'address')
        }),
        ('ID Proof', {
            'fields': ('id_proof',)
        }),
        ('Security', {
            'fields': ('password',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_per_page = 25
    date_hierarchy = 'created_at'


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'stock_status')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('category', 'name')

    def stock_status(self, obj):
        if obj.quantity < 10:
            return 'Low Stock'
        return 'OK'

    stock_status.short_description = 'Status'