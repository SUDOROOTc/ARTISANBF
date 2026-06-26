"""
Vues API pour Artisan BF.

Chaque vue correspond à un endpoint de l'API.
On utilise les "views" de Django REST Framework qui simplifient
la création d'API REST.

Principaux types de vues utilisées :
- APIView : vue de base générique
- ListCreateAPIView : GET(liste) + POST(ajout)
- RetrieveUpdateDestroyAPIView : GET(détail) + PUT(modification) + DELETE
"""

from math import radians, sin, cos, sqrt, atan2
from django.db.models import Q, Count, Avg, F, Value, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User, Categorie, Commerce, Photo, Commentaire
from .serializers import (
    RegisterSerializer, LoginSerializer, ResetPasswordSerializer,
    UserSerializer, CategorieSerializer,
    CommerceListSerializer, CommerceDetailSerializer, CommerceCreateSerializer,
    PhotoSerializer,
    CommentaireSerializer, CommentaireCreateSerializer,
    RechercheSerializer
)
from .permissions import EstProprietaireOuLectureSeule


# ═══════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════

class RegisterView(APIView):
    """
    POST /api/register/
    Inscription d'un nouvel utilisateur.

    Retourne : token d'authentification + infos utilisateur
    """
    # Cette vue est accessible sans authentification
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Crée l'utilisateur
            user = serializer.save()
            # Crée un token d'authentification pour cet utilisateur
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/login/
    Connexion d'un utilisateur existant.

    Retourne : token d'authentification + infos utilisateur
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Crée ou récupère le token existant
            token, _ = Token.objects.get_or_create(user=user)
            # Connecte l'utilisateur dans la session Django
            login(request, user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/logout/
    Déconnexion : supprime le token d'authentification.
    """
    def post(self, request):
        # Supprime le token de l'utilisateur connecté
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Déconnexion réussie.'})


class ResetPasswordView(APIView):
    """
    POST /api/reset-password/
    Réinitialisation simple du mot de passe (Option B).
    L'utilisateur fournit son email et son nouveau mot de passe.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Met à jour le mot de passe (hashe automatiquement)
            user.password = make_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Mot de passe réinitialisé avec succès.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    GET /api/me/
    Retourne le profil de l'utilisateur connecté.
    """
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """
        PATCH /api/me/
        Met à jour partiellement le profil.
        """
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════
# CATÉGORIES
# ═══════════════════════════════════════════════════════════

class CategorieListView(generics.ListAPIView):
    """
    GET /api/categories/
    Liste toutes les catégories avec le nombre de commerces publiés.
    Accessible sans authentification.
    """
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [permissions.AllowAny]


# ═══════════════════════════════════════════════════════════
# COMMERCES
# ═══════════════════════════════════════════════════════════

class CommerceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/commerces/     → Liste de TOUS les commerces publiés
    POST /api/commerces/     → Créer un nouveau commerce
    """
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommerceCreateSerializer
        return CommerceListSerializer

    def get_queryset(self):
        """
        Pour GET : retourne uniquement les commerces publiés.
        """
        return Commerce.objects.filter(est_publie=True).select_related('categorie')

    def perform_create(self, serializer):
        """
        Pour POST : associe automatiquement l'utilisateur connecté
        comme propriétaire du commerce.
        """
        serializer.save(proprietaire=self.request.user)


class MesCommercesView(generics.ListAPIView):
    """
    GET /api/commerces/mes-commerces/
    Liste les commerces de l'utilisateur connecté
    (publiés ET non publiés).
    """
    serializer_class = CommerceListSerializer

    def get_queryset(self):
        return Commerce.objects.filter(
            proprietaire=self.request.user
        ).select_related('categorie')


class CommerceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/commerces/{id}/   → Détail du commerce
    PUT    /api/commerces/{id}/   → Modifier le commerce
    DELETE /api/commerces/{id}/   → Supprimer le commerce
    """
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CommerceCreateSerializer
        return CommerceDetailSerializer

    def get_queryset(self):
        return Commerce.objects.filter(est_publie=True).select_related('categorie', 'proprietaire')

    def perform_update(self, serializer):
        """Vérifie que l'utilisateur est le propriétaire."""
        commerce = self.get_object()
        if commerce.proprietaire != self.request.user:
            return Response(
                {'error': 'Vous n\'êtes pas le propriétaire de ce commerce.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()


class PublierView(APIView):
    """
    PATCH /api/commerces/{id}/publier/
    Rend le commerce visible sur la plateforme.
    Seul le propriétaire peut publier.
    """
    def patch(self, request, pk):
        try:
            commerce = Commerce.objects.get(pk=pk)
        except Commerce.DoesNotExist:
            return Response({'error': 'Commerce introuvable.'}, status=404)

        if commerce.proprietaire != request.user:
            return Response({'error': 'Vous n\'êtes pas le propriétaire.'}, status=403)

        commerce.est_publie = True
        commerce.save()
        return Response({'message': 'Commerce publié avec succès.'})


class RetirerView(APIView):
    """
    PATCH /api/commerces/{id}/retirer/
    Rend le commerce invisible sur la plateforme.
    Seul le propriétaire peut retirer.
    """
    def patch(self, request, pk):
        try:
            commerce = Commerce.objects.get(pk=pk)
        except Commerce.DoesNotExist:
            return Response({'error': 'Commerce introuvable.'}, status=404)

        if commerce.proprietaire != request.user:
            return Response({'error': 'Vous n\'êtes pas le propriétaire.'}, status=403)

        commerce.est_publie = False
        commerce.save()
        return Response({'message': 'Commerce retiré de l\'annuaire.'})


# ═══════════════════════════════════════════════════════════
# PARTAGE WHATSAPP
# ═══════════════════════════════════════════════════════════

class WhatsAppPartageView(APIView):
    """
    GET /api/commerces/{id}/whatsapp-partage/
    Génère l'URL de partage WhatsApp pour un commerce.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            commerce = Commerce.objects.get(pk=pk, est_publie=True)
        except Commerce.DoesNotExist:
            return Response({'error': 'Commerce introuvable.'}, status=404)

        return Response({
            'whatsapp_url': commerce.get_whatsapp_share_url(),
            'message': 'Partagez ce commerce via WhatsApp !'
        })


# ═══════════════════════════════════════════════════════════
# PHOTOS
# ═══════════════════════════════════════════════════════════

class PhotoCreateView(APIView):
    """
    POST /api/commerces/{id}/photos/
    Ajoute une photo à un commerce (max 3 photos).
    """
    # MultiPartParser permet de recevoir des fichiers dans la requête
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, commerce_pk):
        try:
            commerce = Commerce.objects.get(pk=commerce_pk)
        except Commerce.DoesNotExist:
            return Response({'error': 'Commerce introuvable.'}, status=404)

        # Vérifie que l'utilisateur est le propriétaire
        if commerce.proprietaire != request.user:
            return Response({'error': 'Vous n\'êtes pas le propriétaire.'}, status=403)

        # Vérifie la limite de 3 photos
        if commerce.photos.count() >= 3:
            return Response(
                {'error': 'Maximum 3 photos par commerce.'},
                status=400
            )

        # Crée la photo depuis le fichier uploadé
        photo = Photo.objects.create(
            commerce=commerce,
            image=request.FILES.get('image')
        )

        serializer = PhotoSerializer(photo)
        return Response(serializer.data, status=201)


class PhotoDeleteView(APIView):
    """
    DELETE /api/photos/{id}/
    Supprime une photo.
    """
    def delete(self, request, pk):
        try:
            photo = Photo.objects.get(pk=pk)
        except Photo.DoesNotExist:
            return Response({'error': 'Photo introuvable.'}, status=404)

        # Seul le propriétaire du commerce peut supprimer la photo
        if photo.commerce.proprietaire != request.user:
            return Response({'error': 'Vous n\'êtes pas le propriétaire.'}, status=403)

        photo.delete()
        return Response({'message': 'Photo supprimée.'}, status=204)


# ═══════════════════════════════════════════════════════════
# COMMENTAIRES
# ═══════════════════════════════════════════════════════════

class CommentaireListCreateView(APIView):
    """
    GET  /api/commerces/{id}/commentaires/  → Liste des commentaires
    POST /api/commerces/{id}/commentaires/  → Ajouter un commentaire
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, commerce_pk):
        """Retourne la liste des commentaires pour un commerce."""
        commentaires = Commentaire.objects.filter(
            commerce_id=commerce_pk
        ).select_related('auteur')
        serializer = CommentaireSerializer(commentaires, many=True)
        return Response(serializer.data)

    def post(self, request, commerce_pk):
        """Ajoute un commentaire avec notation automatique par IA."""
        try:
            commerce = Commerce.objects.get(pk=commerce_pk, est_publie=True)
        except Commerce.DoesNotExist:
            return Response({'error': 'Commerce introuvable.'}, status=404)

        # Crée le commentaire
        serializer = CommentaireCreateSerializer(data=request.data)
        if serializer.is_valid():
            commentaire = serializer.save(
                commerce=commerce,
                auteur=request.user
            )

            # Calcule la note via l'IA (Async pour ne pas bloquer la réponse)
            self._calculer_note_ia(commentaire)

            # Retourne le commentaire créé
            result = CommentaireSerializer(commentaire).data
            return Response(result, status=201)

        return Response(serializer.errors, status=400)

    def _calculer_note_ia(self, commentaire):
        """
        Calcule la note du commentaire via l'IA OpenRouter,
        puis met à jour la note moyenne du commerce.
        """
        try:
            from .services.notation_ia import noter_commentaire
            note = noter_commentaire(commentaire.texte)
            if note and 1 <= note <= 5:
                commentaire.note = note
                commentaire.save(update_fields=['note'])

                # Recalcule la note moyenne du commerce
                commerce = commentaire.commerce
                resultats = Commentaire.objects.filter(
                    commerce=commerce,
                    note__isnull=False
                ).aggregate(
                    moyenne=Avg('note'),
                    total=Count('id')
                )

                commerce.note_moyenne = round(resultats['moyenne'] or 0.0, 1)
                commerce.nombre_commentaires = resultats['total']
                commerce.save(update_fields=['note_moyenne', 'nombre_commentaires'])
        except Exception as e:
            # Si l'IA échoue, on ne bloque pas la création du commentaire
            print(f"Erreur notation IA: {e}")


# ═══════════════════════════════════════════════════════════
# RECHERCHE GÉOLOCALISÉE
# ═══════════════════════════════════════════════════════════

class RechercheView(APIView):
    """
    GET /api/commerces/recherche/?lat=...&lng=...&categorie=...&nom=...&note_min=...&rayon=...

    Recherche les commerces publiés à proximité d'un point GPS,
    en appliquant les filtres : catégorie, nom, note minimale, rayon.

    Utilise la formule de Haversine pour calculer les distances.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Valide les paramètres de recherche
        params = RechercheSerializer(data=request.query_params)
        if not params.is_valid():
            return Response(params.errors, status=400)

        data = params.validated_data

        # Récupère tous les commerces publiés
        commerces = Commerce.objects.filter(est_publie=True).select_related('categorie')

        # ── Filtre par catégorie ──
        if data.get('categorie'):
            commerces = commerces.filter(
                Q(categorie__slug=data['categorie']) |
                Q(categorie__nom__icontains=data['categorie'])
            )

        # ── Filtre par nom ──
        if data.get('nom'):
            commerces = commerces.filter(nom__icontains=data['nom'])

        # ── Filtre par note minimale ──
        if data.get('note_min'):
            commerces = commerces.filter(note_moyenne__gte=data['note_min'])

        # ── Filtre géographique (si lat/lng fournis) ──
        if data.get('lat') and data.get('lng'):
            lat = float(data['lat'])
            lng = float(data['lng'])
            rayon_km = data.get('rayon', 10)  # Rayon par défaut : 10 km

            # Calcule la distance pour chaque commerce
            resultats = []
            for commerce in commerces:
                distance = self._calculer_distance_haversine(
                    lat, lng,
                    float(commerce.latitude),
                    float(commerce.longitude)
                )
                if distance <= rayon_km:
                    commerce.distance_km = round(distance, 2)
                    resultats.append(commerce)

            # Trie par distance croissante
            resultats.sort(key=lambda c: c.distance_km)

            # Limite à 50 résultats
            resultats = resultats[:50]

            serializer = CommerceListSerializer(resultats, many=True, context={'request': request})
            return Response({
                'count': len(resultats),
                'results': serializer.data
            })

        # ── Sans coordonnées : retourne simplement les résultats filtrés ──
        from rest_framework.settings import api_settings
        paginator = api_settings.DEFAULT_PAGINATION_CLASS()
        page = paginator.paginate_queryset(commerces, request)
        serializer = CommerceListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def _calculer_distance_haversine(self, lat1, lng1, lat2, lng2):
        """
        Calcule la distance en km entre deux points GPS
        en utilisant la formule de Haversine.

        Formule mathématique :
        a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlng/2)
        c = 2 × atan2(√a, √(1-a))
        d = R × c  (où R = rayon terrestre = 6371 km)
        """
        R = 6371  # Rayon de la Terre en km

        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c


# ═══════════════════════════════════════════════════════════
# GESTIONNAIRE DE FICHIERS MÉDIA
# ═══════════════════════════════════════════════════════════

# Note : les fichiers uploadés sont servis via la vue "serve_media"
# dans config/urls.py en développement