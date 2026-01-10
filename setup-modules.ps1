# =============================================================================
# Setup Modules - Configuration automatique des modules
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURATION DES MODULES - Distillation Multicomposants" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Créer la structure de dossiers
Write-Host "[1/5] Création de la structure..." -ForegroundColor Yellow
$folders = @(
    'app',
    'app/core',
    'app/utils',
    'templates',
    'static/css',
    'results',
    'logs',
    'temp_uploads'
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Write-Host "  ✓ Créé: $folder" -ForegroundColor Green
    } else {
        Write-Host "  Existe: $folder" -ForegroundColor Gray
    }
}

# 2. Créer les fichiers __init__.py
Write-Host ""
Write-Host "[2/5] Création des __init__.py..." -ForegroundColor Yellow

@('app', 'app/core', 'app/utils') | ForEach-Object {
    $initFile = "$_/__init__.py"
    if (!(Test-Path $initFile)) {
        New-Item -Path $initFile -ItemType File -Force | Out-Null
        Write-Host "  ✓ Créé: $initFile" -ForegroundColor Green
    }
}

# 3. Instructions pour les modules
Write-Host ""
Write-Host "[3/5] Copie des modules..." -ForegroundColor Yellow
Write-Host ""
Write-Host "ACTION REQUISE:" -ForegroundColor Red
Write-Host "Copier les 3 artifacts suivants dans les fichiers correspondants:" -ForegroundColor White
Write-Host "  1. app/core/compound.py" -ForegroundColor Cyan
Write-Host "  2. app/core/thermodynamics.py" -ForegroundColor Cyan
Write-Host "  3. app/core/shortcut_methods.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Appuyez sur Entrée pour ouvrir les fichiers..." -ForegroundColor Yellow
$null = Read-Host

# Créer et ouvrir les fichiers
Start-Process notepad "app\core\compound.py"
Start-Sleep -Seconds 1
Start-Process notepad "app\core\thermodynamics.py"
Start-Sleep -Seconds 1
Start-Process notepad "app\core\shortcut_methods.py"

Write-Host ""
Write-Host "Appuyez sur Entrée quand les fichiers sont créés..." -ForegroundColor Yellow
$null = Read-Host

# 4. Mettre à jour run-dev.py
Write-Host ""
Write-Host "[4/5] Mise à jour de run-dev.py..." -ForegroundColor Yellow
Write-Host "Le fichier run-dev.py doit importer depuis app.core" -ForegroundColor White
Write-Host "Les imports sont déjà corrects si vous utilisez la version fournie" -ForegroundColor Gray

# 5. Vérification
Write-Host ""
Write-Host "[5/5] Vérification..." -ForegroundColor Yellow

$requiredFiles = @(
    'app/core/compound.py',
    'app/core/thermodynamics.py',
    'app/core/shortcut_methods.py',
    'templates/simulation.html',
    'run-dev.py'
)

$allGood = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        if ($size -gt 100) {
            Write-Host "  ✓ $file ($size bytes)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ $file (trop petit)" -ForegroundColor Yellow
            $allGood = $false
        }
    } else {
        Write-Host "  ✗ $file (manquant)" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host ""
if ($allGood) {
    Write-Host "=============================================================================" -ForegroundColor Green
    Write-Host "  ✅ CONFIGURATION RÉUSSIE" -ForegroundColor Green
    Write-Host "=============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Pour lancer l'application:" -ForegroundColor Yellow
    Write-Host "  python run-dev.py" -ForegroundColor White
} else {
    Write-Host "=============================================================================" -ForegroundColor Red
    Write-Host "  ⚠ CONFIGURATION INCOMPLÈTE" -ForegroundColor Red
    Write-Host "=============================================================================" -ForegroundColor Red
    Write-Host "Complétez les fichiers manquants avant de lancer" -ForegroundColor Yellow
}

Write-Host ""