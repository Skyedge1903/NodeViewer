# Utilisez une image de base Python légère avec la version spécifique demandée
FROM python:3.12.10-slim

# Définissez des variables d'environnement pour éviter les problèmes de buffering et d'encodage
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Créez un répertoire de travail pour l'application
WORKDIR /app

# Copiez d'abord le fichier requirements.txt pour optimiser le caching des layers Docker
COPY requirements.txt .

# Installez les dépendances sans cache pour réduire la taille de l'image
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn  # Assurez-vous que gunicorn est installé si pas déjà dans requirements.txt

# Copiez le reste des fichiers de l'application (cela inclut TOUS les fichiers et répertoires du projet courant)
COPY . .

# Exposez le port par défaut pour Dash (ajustez si nécessaire)
EXPOSE 8050

# Utilisez un utilisateur non-root pour des raisons de sécurité
RUN useradd -m appuser
USER appuser

# Commande de démarrage inspirée de ton Procfile, avec options pour la prod
# --bind pour exposer sur 0.0.0.0:8050 (comme dans ton code original)
# --workers et --timeout : Options recommandées, ajustables
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "4", "--timeout", "120", "app:server"]