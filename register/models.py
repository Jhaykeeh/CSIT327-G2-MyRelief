from django.db import models
import uuid
class Registration(models.Model):
    username = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    contact = models.CharField(max_length=15)
    id_proof_url = models.URLField(blank=True, null=True)
    #id_proof = models.ImageField(upload_to='id_proofs/', blank=True, null=True)
    #id_proof = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.username


class Inventory(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Clothing', 'Clothing'),
        ('Medicine', 'Medicine'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.category})"


class User(models.Model):
        """
        Django model mapped to Supabase 'users' table.
        This enables ORM queries instead of direct API calls.
        """
        userid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        username = models.CharField(max_length=150, unique=True)
        password = models.CharField(max_length=255)  # Will store hashed passwords
        address = models.TextField(blank=True, null=True)
        contact = models.CharField(max_length=20, blank=True, null=True)
        id_proof = models.URLField(max_length=500, blank=True, null=True)
        role = models.CharField(max_length=50, default='FamilyHead')
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        class Meta:
            db_table = 'users'  # Maps to your Supabase 'users' table
            managed = False  # Don't let Django create/modify the table
            ordering = ['-created_at']

        def __str__(self):
            return self.username

        def set_password(self, raw_password):
            """Hash and set password"""
            from django.contrib.auth.hashers import make_password
            self.password = make_password(raw_password)

        def check_password(self, raw_password):
            """Verify password against hash"""
            from django.contrib.auth.hashers import check_password
            return check_password(raw_password, self.password)