"""
Configuration des URLs pour l'application Artisan BF.

Chaque URL correspond à un endpoint de l'API REST.
Les URLs sont organisées par fonctionnalité :
- Authentification (/api/register/, /api/login/, etc.)
- Catégories (/api/categories/)
- Commerces (/api/commerces/)
- Photos (/api/commerces/{id}/photos/)
- Commentaires (/api/commerces/{id}/commentaires/)
- Recherche (/api/commerces/recherche/)
"""

from django.urls import path
from . import views

# Toutes les URLs sont préfixées par /api/ dans config/urls.py
urlpatterns = [
    # ── Authentification ──
    # POST /api/register/ → Inscription
    path('register/', views.RegisterView.as_view(), name='register'),
    # POST /api/login/ → Connexion
    path('login/', views.LoginView.as_view(), name='login'),
    # POST /api/logout/ → Déconnexion
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # POST /api/reset-password/ → Réinitialisation mot de passe
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    # GET /api/me/ → Profil de l'utilisateur connecté
    path('me/', views.MeView.as_view(), name='me'),

    # ── Catégories ──
    # GET /api/categories/ → Liste des catégories
    path('categories/', views.CategorieListView.as_view(), name='categories'),

    # ── Commerces ──
    # GET /api/commerces/ → Liste des commerces publiés
    # POST /api/commerces/ → Créer un commerce
    path('commerces/', views.CommerceListCreateView.as_view(), name='commerce-list'),
    # GET /api/commerces/mes-commerces/ → Mes commerces
    path('commerces/mes-commerces/', views.MesCommercesView.as_view(), name='mes-commerces'),
    # GET /api/commerces/recherche/ → Recherche géolocalisée
    path('commerces/recherche/', views.RechercheView.as_view(), name='recherche'),
    # GET/PUT/DELETE /api/commerces/{id}/ → Détail/modification/suppression
    path('commerces/<int:pk>/', views.CommerceDetailView.as_view(), name='commerce-detail'),
    # PATCH /api/commerces/{id}/publier/ → Publier un commerce
    path('commerces/<int:pk>/publier/', views.PublierView.as_view(), name='commerce-publier'),
    # PATCH /api/commerces/{id}/retirer/ → Retirer un commerce
    path('commerces/<int:pk>/retirer/', views.RetirerView.as_view(), name='commerce-retirer'),
    # GET /api/commerces/{id}/whatsapp-partage/ → Lien WhatsApp
    path('commerces/<int:pk>/whatsapp-partage/', views.WhatsAppPartageView.as_view(), name='whatsapp-partage'),

    # ── Photos ──
    # POST /api/commerces/{commerce_pk}/photos/ → Ajouter une photo
    path('commerces/<int:commerce_pk>/photos/', views.PhotoCreateView.as_view(), name='photo-create'),
    # DELETE /api/photos/{pk}/ → Supprimer une photo
    path('photos/<int:pk>/', views.PhotoDeleteView.as_view(), name='photo-delete'),

    # ── Commentaires ──
    # GET/POST /api/commerces/{commerce_pk}/commentaires/ → Liste/ajout commentaire
    path('commerces/<int:commerce_pk>/commentaires/', views.CommentaireListCreateView.as_view(), name='commentaire-list'),
]