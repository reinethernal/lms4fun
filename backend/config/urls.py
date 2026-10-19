from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from .spa_view import SPAFallbackView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include([
        path('', include('apps.accounts.urls')),
        path('', include('apps.courses.urls')),
        path('', include('apps.lessons.urls')),
        path('', include('apps.tasks.urls')),
        path('', include('apps.submissions.urls')),
        path('', include('apps.gamification.urls')),
        path('', include('apps.imports.urls')),
        path('', include('apps.telegram.urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    from django.views.static import serve

    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]

urlpatterns += [
    re_path(
        r'^(?!api/|django-admin/|static/|media/|assets/).*$',
        SPAFallbackView.as_view(),
        name='spa-fallback',
    ),
]
