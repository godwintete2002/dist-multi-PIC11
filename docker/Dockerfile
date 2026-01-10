# =============================================================================
# Dockerfile Corrigé - Sans problèmes OpenBLAS
# =============================================================================
FROM python:3.11-slim

LABEL maintainer="Prof. BAKHER Zine Elabidine"
LABEL version="2.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

# Installer dépendances système minimales (SANS OpenBLAS problématique)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer répertoire de travail
WORKDIR /app

# Copier requirements
COPY requirements.txt .

# Installer les dépendances Python
# Note: NumPy/SciPy utiliseront leur propre BLAS
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p logs results temp_uploads && \
    chmod -R 755 /app

# Exposer le port
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Commande de démarrage
CMD ["python", "run-dev.py"]