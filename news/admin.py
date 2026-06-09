from django.contrib import admin
from .models import Article
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display=('title','category','is_published','created_at'); prepopulated_fields={'slug':('title',)}; search_fields=('title','body'); list_filter=('category','is_published')
