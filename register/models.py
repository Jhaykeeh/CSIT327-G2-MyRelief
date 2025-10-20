from django.db import models

class Registration(models.Model):
    username = models.CharField(max_length=150, unique=True)
    address = models.TextField()
    contact = models.CharField(max_length=15)
    id_proof = models.FileField(upload_to='id_proofs/')

    def __str__(self):
        return self.username
