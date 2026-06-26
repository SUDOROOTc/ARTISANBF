"""
Service de notation automatique des commentaires par Intelligence Artificielle.

Utilise l'API OpenRouter (gratuite) pour analyser le texte d'un commentaire
et attribuer une note de 1 à 5 étoiles.

Principe :
1. On envoie le texte du commentaire à un modèle d'IA (Llama 3.1 8B)
2. L'IA analyse le sentiment et la qualité du service décrit
3. Elle retourne une note de 1 (très mauvais) à 5 (excellent)
4. Cette note est stockée en base de données

Exemple :
- "Très bon travail, rapide et propre !" → 5
- "Le gars est venu en retard et le travail est bâclé" → 1
- "Bof, ça peut aller" → 3
"""

import requests
import json
import os
import re


def noter_commentaire(texte_commentaire):
    """
    Analyse un commentaire via l'IA et retourne une note de 1 à 5.

    Paramètres :
    - texte_commentaire (str) : Le texte du commentaire à évaluer

    Retourne :
    - int (1-5) : La note attribuée par l'IA
    - None : En cas d'erreur (API indisponible, timeout, etc.)
    """

    # Récupère la clé API et le modèle depuis les settings Django
    # (qui les a chargés depuis le .env)
    from django.conf import settings

    api_key = settings.OPENROUTER_API_KEY
    model = settings.OPENROUTER_MODEL

    # Si pas de clé API, on ne peut pas noter
    if not api_key:
        print("⚠️  Pas de clé API OpenRouter configurée. Notation impossible.")
        return None

    # URL de l'API OpenRouter
    url = "https://openrouter.ai/api/v1/chat/completions"

    # En-têtes HTTP requis par OpenRouter
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Identifie notre application (requis par OpenRouter)
        "HTTP-Referer": "https://github.com/artisan-bf",
        "X-Title": "Artisan BF - Notation Automatique"
    }

    # Message envoyé à l'IA
    # On utilise un "prompt" qui lui demande d'analyser le commentaire
    # et de retourner UNIQUEMENT un chiffre
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un assistant qui évalue des commentaires sur des services "
                    "d'artisans (mécaniciens, couturiers, coiffeurs, etc.) au Burkina Faso. "
                    "Analyse le commentaire et attribue une note de 1 à 5 :\n\n"
                    "1 = Très mauvais (insatisfaction totale, travail bâclé)\n"
                    "2 = Mauvais (plusieurs problèmes)\n"
                    "3 = Moyen (acceptable, ni bon ni mauvais)\n"
                    "4 = Bien (bon travail, le client est satisfait)\n"
                    "5 = Excellent (qualité remarquable, client très satisfait)\n\n"
                    "Réponds UNIQUEMENT par un chiffre (1, 2, 3, 4 ou 5)."
                )
            },
            {
                "role": "user",
                "content": f"Commentaire : \"{texte_commentaire}\"\n\nNote (1-5) :"
            }
        ],
        # Paramètres de l'IA
        "temperature": 0.3,      # Faible température = réponses plus consistantes
        "max_tokens": 10,        # On a besoin que d'un seul chiffre
        "top_p": 0.9
    }

    try:
        # Envoie la requête à OpenRouter
        print(f"🤖 Envoi du commentaire à l'IA pour notation...")
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30  # Timeout de 30 secondes max
        )

        # Vérifie que la requête a réussi
        if response.status_code == 200:
            # Extrait la réponse de l'IA
            resultat = response.json()
            note_texte = resultat['choices'][0]['message']['content'].strip()

            # Extrait le chiffre de la réponse (l'IA pourrait répondre "4" ou "Note: 4")
            note = extraire_nombre(note_texte)

            if note and 1 <= note <= 5:
                print(f"✅ Note attribuée par l'IA : {note}/5")
                return note
            else:
                print(f"⚠️  Réponse de l'IA invalide : '{note_texte}'")
                return None
        else:
            # Si l'API a retourné une erreur
            print(f"❌ Erreur API OpenRouter : {response.status_code} - {response.text}")
            # En mode démo, on attribue une note par défaut basée sur des mots-clés
            return noter_manuellement(texte_commentaire)

    except requests.exceptions.Timeout:
        print("⏱️  Timeout de l'API OpenRouter (30 secondes)")
        return noter_manuellement(texte_commentaire)
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return noter_manuellement(texte_commentaire)


def extraire_nombre(texte):
    """
    Extrait un nombre (1-5) d'un texte.
    L'IA pourrait répondre "4", "Note: 4", "4/5", etc.

    Paramètres :
    - texte (str) : La réponse brute de l'IA

    Retourne :
    - int (1-5) ou None si aucun nombre trouvé
    """
    if not texte:
        return None

    # Cherche un chiffre de 1 à 5 dans le texte
    match = re.search(r'[1-5]', texte)
    if match:
        return int(match.group())
    return None


def noter_manuellement(texte_commentaire):
    """
    [Fallback] Si l'API IA est indisponible, on utilise une méthode simple
    basée sur des mots-clés pour attribuer une note approximative.

    Ce n'est pas aussi précis que l'IA, mais ça permet d'avoir une note
    même hors-ligne.

    Paramètres :
    - texte_commentaire (str) : Le texte du commentaire

    Retourne :
    - int (1-5) : Note estimée
    """
    texte = texte_commentaire.lower()

    # Mots-clés positifs (5 ou 4 étoiles)
    mots_excellents = ['excellent', 'parfait', 'super', 'très satisfait', 'remarquable',
                       'bravo', 'merci beaucoup', 'génial', 'incroyable', 'top']
    mots_bons = ['bien', 'bon', 'satisfait', 'correct', 'propre', 'rapide',
                 'professionnel', 'qualité', 'sympa', 'gentil']

    # Mots-clés négatifs (1 ou 2 étoiles)
    mots_tres_mauvais = ['horrible', 'déplorable', 'arnaque', 'escroc', 'très mauvais',
                         'dégouté', 'honte', 'catastrophe', 'fuyez']
    mots_mauvais = ['mauvais', 'bâclé', 'retard', 'mal fait', 'insatisfait',
                    'cher', 'lent', 'pas content', 'déçu']

    # Mots-clés mitigés (3 étoiles)
    mots_moyens = ['moyen', 'bof', 'peut mieux', 'acceptable', 'passable',
                   'ni bon ni mauvais', 'correct sans plus']

    # Comptage des occurrences
    score = 3  # Note par défaut : 3/5

    for mot in mots_excellents:
        if mot in texte:
            score = 5
            break
    for mot in mots_bons:
        if mot in texte:
            score = max(score, 4)

    for mot in mots_tres_mauvais:
        if mot in texte:
            score = 1
            break
    for mot in mots_mauvais:
        if mot in texte:
            score = min(score, 2)

    for mot in mots_moyens:
        if mot in texte:
            score = min(score, 3)

    print(f"📝 Note manuelle attribuée (fallback) : {score}/5")
    return score