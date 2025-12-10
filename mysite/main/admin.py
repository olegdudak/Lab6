from django.contrib import admin
from .models import Article, News

# Register your models here.

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'date']
    list_filter = ['date']
    search_fields = ['title', 'content']


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'date']
    list_filter = ['date', 'author']
    search_fields = ['title', 'content', 'author']
