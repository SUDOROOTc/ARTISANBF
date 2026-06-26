"""
Permissions personnalisées pour l'API Artisan BF.

Django REST Framework permet de définir des règles d'accès :
- Qui peut voir/créer/modifier/supprimer quoi ?
"""

from rest_framework import permissions


class EstProprietaireOuLectureSeule(permissions.BasePermission):
    """
    Permission : seul le propriétaire d'un commerce peut le modifier/supprimer.
    Les autres utilisateurs peuvent seulement le lire (GET).

    C'est une permission au niveau de l'objet (objet-level permission).
    """

    def has_object_permission(self, request, view, obj):
        """
        Vérifie si l'utilisateur a le droit d'accéder à cet objet spécifique.

        - GET, HEAD, OPTIONS : toujours autorisé (lecture seule)
        - PUT, PATCH, DELETE : seulement si l'utilisateur est le propriétaire
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        # Vérifie que l'utilisateur connecté est le propriétaire
        return obj.proprietaire == request.user