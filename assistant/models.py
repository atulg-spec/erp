from django.db import models

# Create your models here.
class API_Keys(models.Model):
    key = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.key
