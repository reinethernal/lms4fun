from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SPAFallbackView(View):
    """Serve SPA index.html for client-side routes."""

    def get(self, request, *args, **kwargs):
        candidates = [
            Path(settings.BASE_DIR) / 'static' / 'index.html',
            Path(settings.BASE_DIR).parent / 'frontend' / 'dist' / 'index.html',
        ]
        for path in candidates:
            if path.exists():
                return HttpResponse(path.read_text(encoding='utf-8'), content_type='text/html')
        return HttpResponseNotFound('SPA index.html not found. Build the frontend first.')
