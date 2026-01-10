# 🏭 Distillation Multicomposants V2.0

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Plateforme professionnelle de simulation et dimensionnement de colonnes de distillation multicomposants avec interface web moderne, API RESTful et génération de rapports PDF.

**Auteur:** Prof. BAKHER Zine Elabidine  
**Université:** UH1  
**Module:** Modélisation et Simulation des Procédés - PIC

---

## 📋 Table des Matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [API Documentation](#-api-documentation)
- [Déploiement](#-déploiement)
- [Monitoring](#-monitoring)
- [Tests](#-tests)
- [Contributing](#-contributing)

---

## ✨ Fonctionnalités

### 🎯 Simulation Avancée
- **Méthodes Simplifiées**: Fenske, Underwood, Gilliland, Kirkbride
- **Méthodes Rigoureuses**: Résolution MESH complète
- **Thermodynamique**: Support de nombreux composés via la bibliothèque `thermo`
- **Validation**: Validation robuste des données d'entrée

### 🎨 Interface Web Moderne
- **Design Responsive**: Compatible mobile, tablette, desktop
- **Visualisations Interactives**: Graphiques Plotly.js HD
- **UX Optimisée**: Feedback temps réel, animations fluides
- **Progressive Web App**: Installable sur tous les appareils

### 📊 Rapports Professionnels
- **Export PDF**: Génération automatique de rapports détaillés
- **Export JSON**: Données brutes pour post-traitement
- **Graphiques Intégrés**: Charts haute résolution dans les PDF
- **Personnalisation**: Templates modifiables

### 🚀 Performance & Scalabilité
- **Cache Redis**: Mise en cache intelligente des résultats
- **Architecture Moderne**: Flask + Docker + Nginx
- **Load Balancing**: Support horizontal scaling
- **Monitoring**: Prometheus + Grafana intégrés

### 🔒 Sécurité
- **Validation**: Validation stricte des entrées
- **Rate Limiting**: Protection contre les abus
- **HTTPS**: Support SSL/TLS
- **Headers Sécurité**: XSS, CSRF, Clickjacking protection

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX (Reverse Proxy)                 │
│                     Load Balancer & SSL                      │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼────┐            ┌─────▼────┐
│ Flask  │            │  Flask   │  (Horizontal Scaling)
│ Web 1  │            │  Web 2   │
└───┬────┘            └─────┬────┘
    │                       │
    └───────────┬───────────┘
                │
        ┌───────▼────────┐
        │  Redis Cache   │
        │  Session Store │
        └────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      Monitoring Stack                        │
├──────────────┬──────────────────────┬────────────────────────┤
│  Prometheus  │      Grafana         │    Node Exporter      │
│   Metrics    │    Dashboards        │   System Metrics      │
└──────────────┴──────────────────────┴────────────────────────┘
```

### Technologies

| Catégorie | Technologies |
|-----------|-------------|
| **Backend** | Python 3.11, Flask 3.0, NumPy, SciPy |
| **Thermodynamique** | thermo, chemicals, CoolProp |
| **Frontend** | HTML5, TailwindCSS, Plotly.js |
| **Cache** | Redis 7 |
| **Reverse Proxy** | Nginx (Alpine) |
| **Monitoring** | Prometheus, Grafana |
| **Containerisation** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Reports** | ReportLab, Matplotlib |

---

## 📦 Installation

### Prérequis

- **Python** 3.11+
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git**

### Option 1: Installation Locale (Développement)

```bash
# 1. Cloner le repository
git clone https://github.com/votre-username/distillation-multicomposants.git
cd distillation-multicomposants

# 2. Créer un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# 5. Démarrer Redis (requis)
docker run -d -p 6379:6379 redis:7-alpine

# 6. Lancer l'application
python run-dev.py
```

Accéder à: **http://localhost:5000**

### Option 2: Installation Docker (Production-Ready)

```bash
# 1. Cloner le repository
git clone https://github.com/votre-username/distillation-multicomposants.git
cd distillation-multicomposants

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env pour production

# 3. Lancer avec Docker Compose
chmod +x scripts/deploy.sh
./scripts/deploy.sh production

# Ou manuellement:
cd docker
docker-compose up -d
```

**Services disponibles:**
- Application: http://localhost:5000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

---

## 🎮 Utilisation

### Interface Web

1. **Accéder à l'interface**: http://localhost:5000
2. **Configurer la simulation**:
   - Sélectionner les composés (min 2, max 10)
   - Définir le débit d'alimentation (kmol/h)
   - Spécifier la composition (fractions molaires)
   - Ajuster la pression (kPa)
   - Choisir le facteur de reflux
3. **Lancer la simulation**: Cliquer sur "Lancer la Simulation"
4. **Analyser les résultats**: 
   - Visualisations interactives
   - KPIs clés
   - Télécharger le rapport PDF

### Python API (Programmatique)

```python
from app.core.compound import Compound
from app.core.thermodynamics import ThermodynamicPackage
from app.core.shortcut_methods import ShortcutDistillation

# Créer les composés
compounds = [
    Compound('benzene'),
    Compound('toluene'),
    Compound('o-xylene')
]

# Package thermodynamique
thermo = ThermodynamicPackage(compounds)

# Configuration
F = 100.0  # kmol/h
z_F = [0.33, 0.33, 0.34]
P = 101325  # Pa

# Simulation
shortcut = ShortcutDistillation(thermo, F, z_F, P)
results = shortcut.complete_shortcut_design(
    recovery_LK_D=0.95,
    recovery_HK_B=0.95,
    R_factor=1.3,
    efficiency=0.70
)

print(f"Plateaux réels: {results['N_real']}")
print(f"Reflux: {results['R']:.3f}")
```

---

## 📡 API Documentation

### Endpoints Disponibles

#### GET `/health`
**Health Check**

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "2.0.0"
}
```

#### GET `/api/compounds`
**Liste des composés disponibles**

```bash
curl http://localhost:5000/api/compounds
```

**Response:**
```json
{
  "success": true,
  "count": 6,
  "compounds": [
    {"name": "benzene", "Tb": 80.1, "MW": 78.11},
    {"name": "toluene", "Tb": 110.6, "MW": 92.14}
  ]
}
```

#### POST `/api/simulate`
**Lancer une simulation**

```bash
curl -X POST http://localhost:5000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "compounds": ["benzene", "toluene", "o-xylene"],
    "feed_flow": 100,
    "feed_composition": [0.33, 0.33, 0.34],
    "pressure": 101325,
    "reflux_factor": 1.3,
    "efficiency": 0.70
  }'
```

**Response:**
```json
{
  "success": true,
  "from_cache": false,
  "results": {
    "session_id": "20240115_103000",
    "results": {
      "N_min": 6.8,
      "N_real": 19,
      "R_min": 1.85,
      "R": 2.41,
      "feed_stage": 10,
      "D": 33.3,
      "B": 66.7,
      "x_D": [0.95, 0.04, 0.01],
      "x_B": [0.02, 0.48, 0.50]
    }
  }
}
```

#### GET `/api/generate_pdf/{session_id}`
**Télécharger le rapport PDF**

```bash
curl http://localhost:5000/api/generate_pdf/20240115_103000 \
  -o rapport.pdf
```

---

## 🚀 Déploiement

### Déploiement Local

```bash
# Développement
./scripts/deploy.sh development

# Staging
./scripts/deploy.sh staging

# Production
./scripts/deploy.sh production
```

### Déploiement Cloud

#### AWS (ECS/Fargate)

```bash
# 1. Build et push vers ECR
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-1.amazonaws.com

docker tag distillation-app:latest <account-id>.dkr.ecr.eu-west-1.amazonaws.com/distillation-app:latest
docker push <account-id>.dkr.ecr.eu-west-1.amazonaws.com/distillation-app:latest

# 2. Déployer via ECS CLI ou console AWS
```

#### DigitalOcean / Heroku / autres

Voir le guide détaillé dans `/docs/deployment.md`

---

## 📊 Monitoring

### Prometheus

**Accès:** http://localhost:9090

**Métriques disponibles:**
- `http_requests_total`: Total des requêtes HTTP
- `http_request_duration_seconds`: Durée des requêtes
- `redis_connected_clients`: Clients Redis connectés
- `python_info`: Informations Python/Flask

### Grafana

**Accès:** http://localhost:3000  
**Identifiants par défaut:** admin / admin123

**Dashboards pré-configurés:**
- Application Performance Monitoring
- Redis Metrics
- System Resources
- API Usage Statistics

---

## 🧪 Tests

### Lancer les Tests

```bash
# Tests unitaires
pytest tests/ -v

# Tests avec coverage
pytest tests/ --cov=app --cov-report=html

# Tests d'intégration
pytest tests/integration/ -v

# Tests de performance
pytest tests/performance/ --benchmark-only
```

### Tests manuels

```bash
# Test API
curl -X POST http://localhost:5000/api/simulate \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/btx_simulation.json

# Test charge (avec Apache Bench)
ab -n 1000 -c 10 http://localhost:5000/health
```

---

## 🤝 Contributing

Les contributions sont les bienvenues! Suivez ces étapes:

1. **Fork** le projet
2. **Créer une branche**: `git checkout -b feature/amazing-feature`
3. **Commit**: `git commit -m 'Add amazing feature'`
4. **Push**: `git push origin feature/amazing-feature`
5. **Pull Request**

### Standards de Code

- **Python**: PEP 8, type hints, docstrings
- **Tests**: Coverage > 80%
- **Commits**: Messages clairs et descriptifs
- **Documentation**: Mettre à jour si nécessaire

---

## 📝 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍🏫 Auteur & Support

**Prof. BAKHER Zine Elabidine**  
Université UH1  
Module: Modélisation et Simulation des Procédés

**Support:**
- 📧 Email: bakher@uh1.edu
- 💬 Issues: [GitHub Issues](https://github.com/votre-repo/issues)
- 📚 Documentation: [Wiki](https://github.com/votre-repo/wiki)

---

## 🙏 Remerciements

- Bibliothèque [thermo](https://github.com/CalebBell/thermo)
- Communauté Flask
- Contributors et beta testers

---

## 📈 Roadmap

- [ ] Support mélanges non-idéaux (NRTL, UNIQUAC)
- [ ] Simulation MESH rigoureuse complète
- [ ] Interface 3D de la colonne
- [ ] Export vers Aspen Plus
- [ ] API GraphQL
- [ ] Support multi-langues

---

**⭐ Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile!**