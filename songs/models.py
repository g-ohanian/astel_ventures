from django.db import models

from asel_ventures import settings
from user.models import User


# Create your models here.
class Song(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    summary = models.TextField()
    hash_key = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = 'songs'
