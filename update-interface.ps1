# =============================================================================
# Script de Mise à Jour de l'Interface
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "  MISE À JOUR INTERFACE - Distillation Multicomposants" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

$basePath = Get-Location

# Fonction helper
function Log-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Success { param($msg) Write-Host "[✓] $msg" -ForegroundColor Green }
function Log-Error { param($msg) Write-Host "[✗] $msg" -ForegroundColor Red }

# 1. Créer la structure de dossiers
Log-Info "Création de la structure de dossiers..."
$folders = @('templates', 'static', 'static/css', 'static/js', 'logs', 'results', 'temp_uploads')
foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Log-Success "Créé: $folder"
    } else {
        Write-Host "  Existe déjà: $folder" -ForegroundColor Gray
    }
}

Write-Host ""

# 2. Instructions pour l'utilisateur
Write-Host "=============================================================================" -ForegroundColor Yellow
Write-Host "  ACTIONS REQUISES" -ForegroundColor Yellow
Write-Host "=============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "1. METTRE À JOUR templates/simulation.html" -ForegroundColor White
Write-Host "   → Ouvrir: notepad templates\simulation.html" -ForegroundColor Cyan
Write-Host "   → Copier TOUT le contenu de l'artifact 'simulation.html'" -ForegroundColor Cyan
Write-Host "   → Sauvegarder (Ctrl+S)" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. CRÉER static/css/style.css (optionnel)" -ForegroundColor White
Write-Host "   → Ouvrir: notepad static\css\style.css" -ForegroundColor Cyan
Write-Host "   → Copier le contenu de l'artifact 'style.css'" -ForegroundColor Cyan
Write-Host "   → Sauvegarder (Ctrl+S)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Appuyez sur Entrée pour ouvrir les fichiers..." -ForegroundColor Yellow
$null = Read-Host

# Ouvrir les fichiers dans Notepad
Start-Process notepad "templates\simulation.html"
Start-Sleep -Seconds 1
Start-Process notepad "static\css\style.css"

Write-Host ""
Write-Host "Appuyez sur Entrée quand les fichiers sont mis à jour..." -ForegroundColor Yellow
$null = Read-Host

# 3. Vérifier les fichiers
Write-Host ""
Log-Info "Vérification des fichiers..."

if (Test-Path "templates\simulation.html") {
    $size = (Get-Item "templates\simulation.html").Length
    if ($size -gt 1000) {
        Log-Success "simulation.html: OK ($size bytes)"
    } else {
        Log-Error "simulation.html semble incomplet"
    }
} else {
    Log-Error "simulation.html manquant"
}

if (Test-Path "run-dev.py") {
    Log-Success "run-dev.py: OK"
} else {
    Log-Error "run-dev.py manquant"
}

# 4. Vérifier Redis
Write-Host ""
Log-Info "Vérification de Redis..."
$redisRunning = docker ps --filter "name=distillation-redis" --format "{{.Status}}"
if ($redisRunning -like "*Up*") {
    Log-Success "Redis actif"
} else {
    Log-Info "Démarrage de Redis..."
    docker stop distillation-redis 2>$null
    docker rm distillation-redis 2>$null
    docker run -d --name distillation-redis -p 6379:6379 redis:7-alpine redis-server --requirepass changeme123
    Start-Sleep -Seconds 3
    Log-Success "Redis démarré"
}

# 5. Instructions finales
Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Green
Write-Host "  ✅ MISE À JOUR TERMINÉE" -ForegroundColor Green
Write-Host "=============================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Pour lancer l'application:" -ForegroundColor Yellow
Write-Host "  python run-dev.py" -ForegroundColor White
Write-Host ""

Write-Host "Puis ouvrir dans le navigateur:" -ForegroundColor Yellow
Write-Host "  http://localhost:5000" -ForegroundColor White
Write-Host ""

Write-Host "Nouvelles fonctionnalités:" -ForegroundColor Cyan
Write-Host "  ✓ Graphiques corrigés (pas de débordement)" -ForegroundColor White
Write-Host "  ✓ Deux graphiques séparés (Bilans + Compositions)" -ForegroundColor White
Write-Host "  ✓ Tableau détaillé des résultats" -ForegroundColor White
Write-Host "  ✓ Bouton 'Modifier Paramètres' pour relancer" -ForegroundColor White
Write-Host "  ✓ Graphiques exportables en PNG" -ForegroundColor White
Write-Host ""

# Proposer de lancer
$launch = Read-Host "Voulez-vous lancer l'application maintenant? (o/n)"
if ($launch -eq "o" -or $launch -eq "O") {
    Write-Host ""
    Write-Host "Démarrage de l'application..." -ForegroundColor Green
    Write-Host "Appuyez sur Ctrl+C pour arrêter" -ForegroundColor Yellow
    Write-Host ""
    python run-dev.py
}