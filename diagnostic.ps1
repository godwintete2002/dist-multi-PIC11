# =============================================================================
# Script de Diagnostic Docker - PowerShell
# =============================================================================
# Usage: .\diagnostic.ps1
# =============================================================================

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSTIC DOCKER - Distillation Multicomposants" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Vérifier Docker
Write-Host "[1/8] Vérification Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✓ Docker installé: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    exit 1
}

# 2. Vérifier Docker Compose
Write-Host "[2/8] Vérification Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "  ✓ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker Compose non trouvé" -ForegroundColor Red
    exit 1
}

# 3. Vérifier le statut Docker
Write-Host "[3/8] Statut Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "  ✓ Docker daemon actif" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker daemon non démarré" -ForegroundColor Red
    Write-Host "  → Démarrer Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# 4. Vérifier la connexion réseau
Write-Host "[4/8] Test connexion réseau..." -ForegroundColor Yellow
try {
    docker run --rm alpine ping -c 3 google.com | Out-Null
    Write-Host "  ✓ Connexion réseau OK" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Problème de connexion réseau" -ForegroundColor Red
    Write-Host "  → Vérifier proxy/firewall" -ForegroundColor Yellow
}

# 5. Vérifier l'espace disque
Write-Host "[5/8] Espace disque..." -ForegroundColor Yellow
$diskSpace = Get-PSDrive C | Select-Object Used,Free
$freeGB = [math]::Round($diskSpace.Free / 1GB, 2)
if ($freeGB -gt 10) {
    Write-Host "  ✓ Espace libre: $freeGB GB" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Espace libre faible: $freeGB GB" -ForegroundColor Yellow
}

# 6. Lister les images Docker
Write-Host "[6/8] Images Docker existantes..." -ForegroundColor Yellow
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | Select-Object -First 10
Write-Host ""

# 7. Lister les conteneurs
Write-Host "[7/8] Conteneurs actifs..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

# 8. Vérifier les fichiers requis
Write-Host "[8/8] Vérification des fichiers..." -ForegroundColor Yellow
$requiredFiles = @(
    "run-dev.py",
    "requirements.txt",
    "docker\docker-compose.yml"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file manquant" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSTIC TERMINÉ" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# Recommandations
Write-Host "RECOMMANDATIONS:" -ForegroundColor Yellow
Write-Host "1. Si timeout réseau: augmenter les timeouts Docker" -ForegroundColor White
Write-Host "2. Si images manquantes: docker pull redis:7-alpine" -ForegroundColor White
Write-Host "3. Si problème build: utiliser Dockerfile.simple" -ForegroundColor White
Write-Host "4. Si port occupé: netstat -ano | findstr :5000" -ForegroundColor White
Write-Host ""