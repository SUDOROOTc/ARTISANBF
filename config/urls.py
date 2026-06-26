"""
Configuration des URLs principales du projet.

Préfixes :
- /admin/ → Interface d'administration Django
- /api/ → API REST de l'application Artisan BF
- /media/ → Fichiers uploadés (photos) en développement
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),

    # API REST de l'application artisans
    # Tous les endpoints commencent par /api/
    path('api/', include('artisans.urls')),
]

# En mode développement, on sert les fichiers média (photos) directement
# via Django. En production, on utiliserait un vrai serveur (Nginx, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)