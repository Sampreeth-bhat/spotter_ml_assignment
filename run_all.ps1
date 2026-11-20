# ============================================================
# Freight Rate Prediction — Full Pipeline Runner
# Run from project root with:
#   .\run_all.ps1
# ============================================================

Write-Host "=== Freight Rate Prediction Pipeline ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: EDA
Write-Host "[1/4] Running EDA..." -ForegroundColor Yellow
.\venv\Scripts\python.exe src\eda.py
if ($LASTEXITCODE -ne 0) { Write-Error "EDA failed"; exit 1 }

# Step 2: Train model
Write-Host ""
Write-Host "[2/4] Training model..." -ForegroundColor Yellow
.\venv\Scripts\python.exe src\train.py
if ($LASTEXITCODE -ne 0) { Write-Error "Training failed"; exit 1 }

# Step 3: Generate predictions
Write-Host ""
Write-Host "[3/4] Generating predictions..." -ForegroundColor Yellow
.\venv\Scripts\python.exe src\predict.py
if ($LASTEXITCODE -ne 0) { Write-Error "Prediction failed"; exit 1 }

# Step 4: Score
Write-Host ""
Write-Host "[4/4] Running scorer..." -ForegroundColor Yellow
.\venv\Scripts\python.exe score.py --predictions validation_predictions.csv --december-predictions december-chart-inputs.csv
if ($LASTEXITCODE -ne 0) { Write-Error "Scorer failed"; exit 1 }

Write-Host ""
Write-Host "=== PIPELINE COMPLETE ===" -ForegroundColor Green
Write-Host "Outputs:"
Write-Host "  validation_predictions.csv"
Write-Host "  december-chart-inputs.csv (filled)"
Write-Host "  scorer_results/candidate_december.png"
