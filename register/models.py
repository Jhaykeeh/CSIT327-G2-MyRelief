from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, firstname, lastname, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, firstname=firstname, lastname=lastname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, firstname, lastname, password=None, **extra_fields):
        extra_fields.setdefault('role', 'Admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, firstname, lastname, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('FamilyHead', 'Family Head'),
        ('Admin', 'Administrator'),
    ]
    
    userid = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100, default='Unknown')
    barangay = models.CharField(max_length=100, default='Unknown')
    contact = models.CharField(max_length=15)
    password = models.CharField(max_length=128)  # Using Django's password hashing
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FamilyHead')
    
    # Required for Django admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['firstname', 'lastname']
    
    def save(self, *args, **kwargs):
        # Automatically set is_staff based on role
        if self.role == 'Admin':
            self.is_staff = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.username})"


class Inventory(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Clothing', 'Clothing'),
        ('Medicine', 'Medicine'),
        ('Hygiene', 'Hygiene'),
        ('Shelter', 'Shelter'),
        ('Others', 'Others'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.category})"
    
    class Meta:
        verbose_name_plural = "Inventory Items"
        ordering = ['-created_at']


class ReliefDistribution(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='distributions')
    item = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='distributions')
    quantity_distributed = models.PositiveIntegerField()
    distribution_date = models.DateTimeField(auto_now_add=True)
    distributed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='distributed_items')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.item.name} ({self.quantity_distributed})"
    
    class Meta:
        verbose_name_plural = "Relief Distributions"
        ordering = ['-distribution_date']


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_user', 'New User Registration'),
        ('low_stock', 'Low Stock Alert'),
        ('distribution', 'Relief Distribution'),
        ('update', 'System Update'),
    ]
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']


# Signal to create notification when new user registers
@receiver(post_save, sender=User)
def create_user_notification(sender, instance, created, **kwargs):
    if created and instance.role == 'FamilyHead':
        Notification.objects.create(
            notification_type='new_user',
            title='New User Registration',
            message=f'New family head registered: {instance.firstname} {instance.lastname} ({instance.username})',
            related_user=instance
        )


# Signal to create notification when inventory is low
@receiver(post_save, sender=Inventory)
def check_inventory_stock(sender, instance, **kwargs):
    if instance.quantity <= 10 and instance.quantity > 0:
        # Check if notification already exists for this item
        existing = Notification.objects.filter(
            notification_type='low_stock',
            message__contains=instance.name,
            is_read=False
        ).exists()
        
        if not existing:
            Notification.objects.create(
                notification_type='low_stock',
                title='Low Stock Alert',
                message=f'Inventory item "{instance.name}" is running low. Only {instance.quantity} items remaining.'
            )


# Signal to create notification when distribution happens
@receiver(post_save, sender=ReliefDistribution)
def create_distribution_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            notification_type='distribution',
            title='Relief Distribution',
            message=f'{instance.item.name} distributed to {instance.user.firstname} {instance.user.lastname} ({instance.quantity_distributed} items)',
            related_user=instance.user
        )
