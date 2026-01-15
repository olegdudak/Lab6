from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Article(models.Model):
    CATEGORY_CHOICES = [
        ('memes', 'Меми'),
        ('pupils', 'Учні'),
        ('other', 'Інше'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='memes')
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']
        verbose_name = "Новина"
        verbose_name_plural = "Новини"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}..."

    class Meta:
        ordering = ['-timestamp']
