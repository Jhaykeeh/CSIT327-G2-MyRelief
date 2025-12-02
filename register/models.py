from django.db import models

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
#ORM FOR LOGIN
class Login(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username
#ORM for Admin
class AdminLogin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.username