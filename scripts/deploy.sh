#!/bin/bash
# =============================================================================
# Script de Déploiement Automatisé - Distillation Multicomposants
# =============================================================================
# Usage:
#   ./scripts/deploy.sh [environment]
#   environment: development, staging, production (default: development)
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="distillation-multicomposants"
DOCKER_IMAGE="distillation-app"
ENVIRONMENT="${1:-development}"
VERSION=$(date +%Y%m%d-%H%M%S)

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     DÉPLOIEMENT - DISTILLATION MULTICOMPOSANTS V2.0           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Environnement: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}Version: ${VERSION}${NC}"
echo ""

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    log_success "Docker: OK"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    log_success "Docker Compose: OK"
    
    # Check .env file
    if [ ! -f ".env" ] && [ "$ENVIRONMENT" = "production" ]; then
        log_error "Fichier .env manquant pour production"
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
    echo ""
}

run_tests() {
    log_info "Exécution des tests..."
    
    if [ -d "tests" ]; then
        # Run tests in Docker
        docker run --rm \
            -v $(pwd):/app \
            -w /app \
            python:3.11-slim \
            bash -c "pip install -q pytest && pytest tests/ -v" || {
            log_error "Tests échoués"
            exit 1
        }
        log_success "Tests réussis"
    else
        log_warning "Aucun test trouvé, passage..."
    fi
    echo ""
}

build_docker_image() {
    log_info "Construction de l'image Docker..."
    
    docker build \
        -t ${DOCKER_IMAGE}:${VERSION} \
        -t ${DOCKER_IMAGE}:latest \
        -f docker/Dockerfile \
        --build-arg ENVIRONMENT=${ENVIRONMENT} \
        . || {
        log_error "Échec de la construction"
        exit 1
    }
    
    log_success "Image construite: ${DOCKER_IMAGE}:${VERSION}"
    echo ""
}

stop_services() {
    log_info "Arrêt des services existants..."
    
    cd docker
    docker-compose down || true
    cd ..
    
    log_success "Services arrêtés"
    echo ""
}

start_services() {
    log_info "Démarrage des services..."
    
    cd docker
    
    # Set environment
    export ENVIRONMENT=${ENVIRONMENT}
    
    # Start services
    docker-compose up -d || {
        log_error "Échec du démarrage"
        exit 1
    }
    
    cd ..
    
    log_success "Services démarrés"
    echo ""
}

wait_for_health() {
    log_info "Attente de la disponibilité des services..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -sf http://localhost:5000/health > /dev/null 2>&1; then
            log_success "Application prête"
            return 0
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        echo -n "."
        sleep 2
    done
    
    log_error "Timeout: l'application n'a pas démarré"
    return 1
}

run_migrations() {
    log_info "Exécution des migrations..."
    
    # Add migration logic here if needed
    # docker exec distillation-web python manage.py migrate
    
    log_success "Migrations terminées"
    echo ""
}

display_status() {
    log_info "Statut des services:"
    echo ""
    
    cd docker
    docker-compose ps
    cd ..
    
    echo ""
}

display_urls() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    DÉPLOIEMENT RÉUSSI ✓                       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}URLs disponibles:${NC}"
    echo -e "  🌐 Application Web:     http://localhost:5000"
    echo -e "  📊 Grafana:            http://localhost:3000"
    echo -e "  📈 Prometheus:         http://localhost:9090"
    echo -e "  🔍 Health Check:       http://localhost:5000/health"
    echo ""
    echo -e "${BLUE}Commandes utiles:${NC}"
    echo -e "  📋 Logs:               docker-compose -f docker/docker-compose.yml logs -f web"
    echo -e "  🛑 Arrêter:           docker-compose -f docker/docker-compose.yml down"
    echo -e "  🔄 Redémarrer:        docker-compose -f docker/docker-compose.yml restart"
    echo -e "  📊 Monitoring:         docker stats"
    echo ""
}

backup_data() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Sauvegarde des données..."
        
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup volumes
        docker run --rm \
            -v distillation_redis_data:/data \
            -v $(pwd)/$BACKUP_DIR:/backup \
            alpine tar czf /backup/redis_data.tar.gz /data
        
        log_success "Sauvegarde créée: $BACKUP_DIR"
        echo ""
    fi
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

main() {
    echo -e "${BLUE}🚀 Début du déploiement...${NC}"
    echo ""
    
    # 1. Check prerequisites
    check_prerequisites
    
    # 2. Backup (production only)
    if [ "$ENVIRONMENT" = "production" ]; then
        backup_data
    fi
    
    # 3. Run tests
    if [ "$ENVIRONMENT" != "development" ]; then
        run_tests
    fi
    
    # 4. Build Docker image
    build_docker_image
    
    # 5. Stop existing services
    stop_services
    
    # 6. Start new services
    start_services
    
    # 7. Wait for health
    wait_for_health
    
    # 8. Run migrations
    run_migrations
    
    # 9. Display status
    display_status
    
    # 10. Display URLs
    display_urls
    
    log_success "Déploiement terminé avec succès!"
}

# =============================================================================
# Cleanup on Error
# =============================================================================

cleanup() {
    log_error "Erreur lors du déploiement!"
    log_info "Nettoyage..."
    
    cd docker
    docker-compose logs --tail=50 web
    cd ..
    
    exit 1
}

trap cleanup ERR

# =============================================================================
# Execute
# =============================================================================

main "$@"