"""
Configuration de l'interface d'administration Django pour l'app artisans.
Permet de gérer les données via /admin/ pendant le développement.
"""

from django.contrib import admin
from .models import User, Categorie, Commerce, Photo, Commentaire


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Configuration de l'affichage des utilisateurs dans l'admin.
    """
    # Colonnes affichées dans la liste
    list_display = ('username', 'email', 'phone', 'is_active', 'date_joined')
    # Champs sur lesquels on peut filtrer (barre latérale droite)
    list_filter = ('is_active', 'date_joined')
    # Champs de recherche (barre de recherche en haut)
    search_fields = ('username', 'email', 'phone')


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    """
    Configuration de l'affichage des catégories dans l'admin.
    """
    list_display = ('nom', 'slug', 'icone')
    prepopulated_fields = {'slug': ('nom',)}  # Slug auto-rempli


class PhotoInline(admin.TabularInline):
    """
    Permet d'ajouter/modifier des photos directement
    depuis la page d'édition d'un commerce.
    """
    model = Photo
    extra = 1  # Affiche 1 ligne vide pour ajouter une photo


class CommentaireInline(admin.TabularInline):
    """
    Permet de voir les commentaires depuis la page d'édition d'un commerce.
    """
    model = Commentaire
    extra = 0
    readonly_fields = ('note',)  # La note est en lecture seule (calculée par IA)


@admin.register(Commerce)
class CommerceAdmin(admin.ModelAdmin):
    """
    Configuration de l'affichage des commerces dans l'admin.
    """
    list_display = ('nom', 'categorie', 'proprietaire', 'est_publie', 'note_moyenne', 'created_at')
    list_filter = ('est_publie', 'categorie')
    search_fields = ('nom', 'telephone', 'adresse_description')
    # Affiche les photos et commentaires liés
    inlines = [PhotoInline, CommentaireInline]


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """
    Configuration de l'affichage des photos dans l'admin.
    """
    list_display = ('id', 'commerce', 'uploaded_at')
    list_filter = ('uploaded_at',)


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    """
    Configuration de l'affichage des commentaires dans l'admin.
    """
    list_display = ('auteur', 'commerce', 'note', 'created_at')
    list_filter = ('note', 'created_at')
    search_fields = ('texte',)
    readonly_fields = ('note',)  # La note est calculée par l'IA, pas modifiable