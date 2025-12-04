from django.db import models

class Registration(models.Model):
    username = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    contact = models.CharField(max_length=15)
    city = models.CharField(max_length=100, default='')
    barangay = models.CharField(max_length=100, default='')
    id_proof_url = models.URLField(blank=True, null=True)

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


class Login(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username


class AdminLogin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username
