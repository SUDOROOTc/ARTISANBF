"""
Sérialiseurs (Serializers) pour l'API Artisan BF.

Un sérialiseur convertit les données :
- Python → JSON (quand on envoie une réponse à l'utilisateur)
- JSON → Python (quand on reçoit une requête de l'utilisateur)

Il valide aussi les données avant de les sauvegarder.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import User, Categorie, Commerce, Photo, Commentaire


# ─── SÉRIALISEUR UTILISATEUR ─────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription d'un nouvel utilisateur.
    """
    # On déclare password en écriture seule (ne sera jamais renvoyé en JSON)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]  # Applique les validateurs Django (longueur min, etc.)
    )
    # Confirmation du mot de passe (pas stocké en base, juste pour validation)
    password2 = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        # Champs requis pour l'inscription
        fields = ('username', 'email', 'phone', 'password', 'password2', 'first_name', 'last_name')

    def validate(self, attrs):
        """
        Validation personnalisée :
        - Vérifie que les deux mots de passe correspondent
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Les mots de passe ne correspondent pas.'
            })
        return attrs

    def create(self, validated_data):
        """
        Crée l'utilisateur après validation.
        On retire password2 (qui n'est pas un champ du modèle),
        puis on utilise create_user (qui hashe le mot de passe automatiquement).
        """
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Sérialiseur pour la connexion.
    N'hérite PAS de ModelSerializer car on ne crée pas d'objet,
    on vérifie juste les identifiants.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Vérifie que le couple username/password est correct.
        """
        user = authenticate(
            username=attrs['username'],
            password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError('Identifiants incorrects.')
        if not user.is_active:
            raise serializers.ValidationError('Ce compte est désactivé.')
        # On stocke l'utilisateur dans les données validées
        # pour pouvoir y accéder dans la vue
        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """
    Sérialiseur pour la réinitialisation de mot de passe.
    L'utilisateur fournit son email et son nouveau mot de passe.
    """
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate(self, attrs):
        """
        Vérifie que l'email existe dans la base.
        """
        try:
            user = User.objects.get(email=attrs['email'])
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError('Aucun compte avec cet email.')
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher/modifier le profil utilisateur.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name', 'quartier')
        read_only_fields = ('id',)  # id ne peut pas être modifié


# ─── SÉRIALISEUR CATÉGORIE ───────────────────────────────

class CategorieSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simple pour lister les catégories.
    """
    # Nombre de commerces publiés dans cette catégorie (champ calculé)
    nombre_commerces = serializers.SerializerMethodField()

    class Meta:
        model = Categorie
        fields = ('id', 'nom', 'slug', 'icone', 'nombre_commerces')

    def get_nombre_commerces(self, obj):
        """
        Calcule le nombre de commerces publiés pour cette catégorie.
        """
        return obj.commerces.filter(est_publie=True).count()


# ─── SÉRIALISEUR PHOTO ────────────────────────────────────

class PhotoSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les photos.
    Affiche l'URL complète de l'image.
    """
    class Meta:
        model = Photo
        fields = ('id', 'image', 'uploaded_at')
        read_only_fields = ('id', 'uploaded_at')


# ─── SÉRIALISEUR COMMENTAIRE ──────────────────────────────

class CommentaireSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les commentaires.
    """
    # On affiche le nom de l'auteur (pas seulement son ID)
    auteur_nom = serializers.CharField(source='auteur.username', read_only=True)

    class Meta:
        model = Commentaire
        fields = ('id', 'auteur', 'auteur_nom', 'texte', 'note', 'created_at')
        read_only_fields = ('id', 'auteur', 'note', 'created_at')


class CommentaireCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la CRÉATION d'un commentaire.
    L'utilisateur fournit seulement le texte.
    La note sera calculée par l'IA après création.
    """
    class Meta:
        model = Commentaire
        fields = ('texte',)


# ─── SÉRIALISEUR COMMERCE ─────────────────────────────────

class CommerceListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la LISTE des commerces (vue succincte).
    """
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    categorie_icone = serializers.CharField(source='categorie.icone', read_only=True)
    nombre_photos = serializers.SerializerMethodField()
    # Distance estimée (sera remplie par la recherche)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Commerce
        fields = (
            'id', 'nom', 'categorie', 'categorie_nom', 'categorie_icone',
            'latitude', 'longitude', 'telephone', 'adresse_description',
            'est_publie', 'note_moyenne', 'nombre_commentaires',
            'nombre_photos', 'distance_km', 'created_at'
        )

    def get_nombre_photos(self, obj):
        return obj.photos.count()

    def get_distance_km(self, obj):
        """
        Récupère la distance calculée par la vue de recherche.
        Vient du context passé à la requête.
        """
        return getattr(obj, 'distance_km', None)


class CommerceDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le DÉTAIL d'un commerce (avec photos et infos complètes).
    """
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    categorie_icone = serializers.CharField(source='categorie.icone', read_only=True)
    proprietaire_nom = serializers.CharField(source='proprietaire.username', read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    whatsapp_url = serializers.SerializerMethodField()

    class Meta:
        model = Commerce
        fields = (
            'id', 'proprietaire', 'proprietaire_nom',
            'nom', 'categorie', 'categorie_nom', 'categorie_icone',
            'latitude', 'longitude', 'telephone', 'adresse_description',
            'heure_ouverture', 'heure_fermeture',
            'est_publie', 'note_moyenne', 'nombre_commentaires',
            'photos', 'whatsapp_url',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'proprietaire', 'proprietaire_nom', 'note_moyenne',
                           'nombre_commentaires', 'created_at', 'updated_at')

    def get_whatsapp_url(self, obj):
        """Génère l'URL de partage WhatsApp."""
        return obj.get_whatsapp_share_url()


class CommerceCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la CRÉATION d'un commerce.
    """
    class Meta:
        model = Commerce
        fields = (
            'nom', 'categorie', 'latitude', 'longitude',
            'telephone', 'adresse_description',
            'heure_ouverture', 'heure_fermeture'
        )

    def validate_latitude(self, value):
        """Valide que la latitude est dans les limites du Burkina Faso."""
        # Burkina Faso : entre 9° et 15° de latitude Nord
        if value < 9 or value > 15:
            raise serializers.ValidationError(
                'La latitude doit être comprise entre 9 et 15 (Burkina Faso).'
            )
        return value

    def validate_longitude(self, value):
        """Valide que la longitude est dans les limites du Burkina Faso."""
        # Burkina Faso : entre -5° et 3° de longitude
        if value < -5 or value > 3:
            raise serializers.ValidationError(
                'La longitude doit être comprise entre -5 et 3 (Burkina Faso).'
            )
        return value


# ─── SÉRIALISEUR RECHERCHE ────────────────────────────────

class RechercheSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider les paramètres de recherche.
    """
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    rayon = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
    categorie = serializers.CharField(required=False)
    nom = serializers.CharField(required=False)
    note_min = serializers.IntegerField(required=False, min_value=1, max_value=5)