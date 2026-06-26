FROM python:3.14-slim

# Empêche Python de bufferiser les logs (utile pour voir les logs en direct avec docker compose logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dépendances système minimales (build tools pour certains packages Python, ex: Pillow pour les photos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement requirements d'abord -> permet à Docker de cacher cette étape
# si seul le code change (build plus rapide sur les rebuilds suivants)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]