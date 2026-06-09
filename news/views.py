from django.shortcuts import get_object_or_404, render
from .models import Article


def news_list(request):
    return render(
        request,
        "news/list.html",
        {"articles": Article.objects.filter(is_published=True)},
    )


def news_detail(request, slug):
    return render(
        request,
        "news/detail.html",
        {"article": get_object_or_404(Article, slug=slug, is_published=True)},
    )
