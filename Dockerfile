FROM python:3.12-slim

# Variables d'environnement pour optimiser Python et configurer le port
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    UV_SYSTEM_PYTHON=1

# Installation de curl pour les healthchecks optionnels
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Astral uv (le gestionnaire de packages ultra-rapide utilisé par le projet)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Définition du répertoire de travail principal
WORKDIR /app

# Copie des fichiers de configuration des dépendances
COPY pyproject.toml uv.lock ./

# Synchronisation et installation des dépendances du projet (sans les dépendances dev)
# uv sync va créer un environnement virtuel dans /app/.venv
RUN uv sync --frozen --no-cache

# Copie du code source et des répertoires nécessaires
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/

# Créer un utilisateur non-root pour des raisons de sécurité en production (Best Practice OWASP/MLOps)
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposition du port
EXPOSE 8000

# Commande de démarrage avec uvicorn en utilisant le venv synchronisé
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
