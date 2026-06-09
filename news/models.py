from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Article(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=80, default="Event Update")
    excerpt = models.TextField(max_length=300)
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news_detail", args=[self.slug])

    def __str__(self):
        return self.title
