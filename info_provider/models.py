from django.db import models

# Create your models here.
class PasswordKeeper(models.Model):
	name = models.CharField(max_length=100)
	private_key = models.TextField()
	public_key = models.TextField(null=True, blank=True)
	crypto_type = models.CharField(max_length = 25)
