"""
Modèles de données pour l'annuaire Artisan BF.

Contient :
- User : Compte utilisateur étendu avec téléphone
- Categorie : Métier/domaine d'activité (mécanicien, couturier, etc.)
- Commerce : Fiche d'établissement d'un artisan
- Photo : 1 à 3 photos par commerce
- Commentaire : Avis client avec note calculée par IA
"""

import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


# ─── MODÈLE USER ───────────────────────────────────────────
class User(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    On hérite de AbstractUser pour garder le système d'authentification Django
    (email, password, username) mais on ajoute un champ téléphone obligatoire.

    AbstractUser fournit déjà :
    - username, first_name, last_name, email, password
    - is_staff, is_active, is_superuser
    - date_joined, last_login
    """

    # Numéro de téléphone unique (ex: +226 70 12 34 56 pour le Burkina)
    # On utilise CharField car on ne fait pas d'opérations mathématiques dessus
    phone = models.CharField(
        max_length=20,
        unique=True,  # Pas deux utilisateurs avec le même numéro
        verbose_name="Téléphone"
    )

    # Quartier de résidence (optionnel, peut aider pour la recherche)
    quartier = models.CharField(
        max_length=100,
        blank=True,   # Champ optionnel dans les formulaires
        null=True,    # Autorise NULL en base de données
        verbose_name="Quartier"
    )

    # Date de création du compte (auto-ajoutée à l'insertion)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )

    # Date de dernière modification (auto-ajoutée à chaque sauvegarde)
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    class Meta:
        # Nom affiché dans l'interface d'administration
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        # Trie les utilisateurs par date d'inscription décroissante
        ordering = ['-created_at']

    def __str__(self):
        """
        Représentation textuelle de l'utilisateur.
        Affiche le nom complet ou le pseudo si disponible.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.phone})"
        return f"{self.username} ({self.phone})"


# ─── MODÈLE CATEGORIE ──────────────────────────────────────
class Categorie(models.Model):
    """
    Catégorie de métier (ex: Mécanicien, Couturier, Coiffeur, Soudeur, etc.)
    Sera pré-remplie avec les catégories de base.
    """

    # Nom de la catégorie (ex: "Mécanicien auto")
    nom = models.CharField(
        max_length=100,
        unique=True,  # Pas deux catégories avec le même nom
        verbose_name="Nom de la catégorie"
    )

    # Slug : version URL-friendly du nom (ex: "mecanicien-auto")
    # Utilisé pour les filtres de recherche
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,  # On le calcule automatiquement
        verbose_name="Slug"
    )

    # Icône (emoji ou classe CSS) pour l'affichage sur le frontend
    icone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icône"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']  # Tri alphabétique

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save().
        Si le slug n'est pas fourni, on le génère automatiquement
        à partir du nom (ex: "Mécanicien Auto" → "mecanicien-auto").
        """
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


# ─── MODÈLE COMMERCE ───────────────────────────────────────
class Commerce(models.Model):
    """
    Fiche d'établissement d'un artisan/commerce.
    C'est le coeur de l'application.
    """

    # Relation avec l'utilisateur propriétaire
    # CASCADE = si l'utilisateur est supprimé, ses commerces aussi
    proprietaire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commerces',  # Permet de faire user.commerces.all()
        verbose_name="Propriétaire"
    )

    # Nom commercial (ex: "Garage Amadou", "Couture Fatima")
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom du commerce"
    )

    # Catégorie du commerce
    # PROTECT = empêche de supprimer une catégorie si des commerces l'utilisent
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='commerces',
        verbose_name="Catégorie"
    )

    # Position GPS : latitude (précision 6 décimales = ~11 cm)
    latitude = models.DecimalField(
        max_digits=9,      # Ex: 12.345678
        decimal_places=6,
        verbose_name="Latitude"
    )

    # Position GPS : longitude
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Longitude"
    )

    # Numéro de téléphone direct (pour le bouton "Appeler")
    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone"
    )

    # Description textuelle de l'adresse (ex: "À côté du marché, près de la mosquée")
    adresse_description = models.TextField(
        verbose_name="Description de l'adresse"
    )

    # Horaire d'ouverture (optionnel)
    heure_ouverture = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Heure d'ouverture"
    )

    # Horaire de fermeture (optionnel)
    heure_fermeture = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Heure de fermeture"
    )

    # Statut de publication
    # False = invisible sur la plateforme (brouillon)
    est_publie = models.BooleanField(
        default=False,
        verbose_name="Publié"
    )

    # Note moyenne calculée automatiquement à partir des commentaires
    note_moyenne = models.FloatField(
        default=0.0,
        verbose_name="Note moyenne"
    )

    # Nombre total de commentaires (pour éviter de faire un count() à chaque fois)
    nombre_commentaires = models.IntegerField(
        default=0,
        verbose_name="Nombre de commentaires"
    )

    # Métadonnées temporelles
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière modification"
    )

    class Meta:
        verbose_name = "Commerce"
        verbose_name_plural = "Commerces"
        # Trie par défaut : les plus récents d'abord
        ordering = ['-created_at']
        # Index pour accélérer les recherches par catégorie et statut
        indexes = [
            models.Index(fields=['categorie', 'est_publie']),
            models.Index(fields=['nom']),
        ]

    def __str__(self):
        return f"{self.nom} - {self.categorie.nom}"

    def get_coordinates(self):
        """
        Retourne les coordonnées GPS sous forme de tuple.
        Utile pour les calculs de distance.
        """
        return (float(self.latitude), float(self.longitude))

    def get_whatsapp_share_url(self):
        """
        Génère l'URL de partage WhatsApp pour ce commerce.
        Format: https://wa.me/226XXXXXXXXX?text=...
        L'utilisateur peut cliquer pour partager l'adresse.
        """
        # Numéro au format international (sans le +)
        numero = self.telephone.replace(' ', '').replace('+', '')
        message = (
            f"*{self.nom}*\n"
            f"{self.categorie.nom}\n"
            f"📍 {self.adresse_description}\n"
            f"📞 {self.telephone}\n\n"
            f"Voir sur Google Maps: "
            f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        )
        from urllib.parse import quote
        return f"https://wa.me/{numero}?text={quote(message)}"


# ─── MODÈLE PHOTO ──────────────────────────────────────────
class Photo(models.Model):
    """
    Photo d'un commerce (1 à 3 photos maximum).
    """

    # Relation avec le commerce
    commerce = models.ForeignKey(
        Commerce,
        on_delete=models.CASCADE,
        related_name='photos',  # Permet de faire commerce.photos.all()
        verbose_name="Commerce"
    )

    # Le fichier image lui-même
    # upload_to = sous-dossier dans media/ organisé par commerce
    image = models.ImageField(
        upload_to='photos/commerces/',
        verbose_name="Image"
    )

    # Date d'upload
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'upload"
    )

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        return f"Photo de {self.commerce.nom} (uploadée le {self.uploaded_at})"


# ─── MODÈLE COMMENTAIRE ────────────────────────────────────
class Commentaire(models.Model):
    """
    Commentaire laissé par un utilisateur sur un commerce.
    La note (1-5) est calculée automatiquement par l'IA via OpenRouter.
    """

    # Commerce concerné
    commerce = models.ForeignKey(
        Commerce,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Commerce"
    )

    # Auteur du commentaire
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name="Auteur"
    )

    # Contenu textuel du commentaire
    texte = models.TextField(
        verbose_name="Commentaire"
    )

    # Note attribuée par l'IA (1-5)
    # null=True car elle est calculée après la création
    note = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Note (1-5)"
    )

    # Date de création
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date du commentaire"
    )

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        # Trie du plus récent au plus ancien
        ordering = ['-created_at']

    def __str__(self):
        return f"Commentaire de {self.auteur.username} sur {self.commerce.nom}"