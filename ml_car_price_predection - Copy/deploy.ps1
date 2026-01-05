# Deployment script for ML Car Price Prediction
# Usage: .\deploy.ps1 -Env dev -Action up

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev','sit','uat','prod')]
    [string]$Env = 'dev',
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('up','down','restart','logs','status','scale','backup')]
    [string]$Action = 'up',
    
    [Parameter(Mandatory=$false)]
    [string]$Service = '',
    
    [Parameter(Mandatory=$false)]
    [int]$Replicas = 3
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }

$composeFile = "deployment\$Env\docker-compose.$Env.yml"

if (-not (Test-Path $composeFile)) {
    Write-Error "Error: Compose file not found: $composeFile"
    exit 1
}

Write-Success "========================================"
Write-Success "ML Car Price Prediction - Deployment"
Write-Success "========================================"
Write-Info "Environment: $Env"
Write-Info "Action: $Action"
Write-Success "========================================"

switch ($Action) {
    'up' {
        Write-Warning "Starting services..."
        
        # Production requires secrets
        if ($Env -eq 'prod') {
            if (-not $env:PROD_DB_PASSWORD -or -not $env:REDIS_PASSWORD) {
                Write-Error "Error: Production secrets not set!"
                Write-Host "Please set environment variables:"
                Write-Host "  `$env:PROD_DB_PASSWORD = 'your_password'"
                Write-Host "  `$env:REDIS_PASSWORD = 'your_password'"
                Write-Host "  `$env:JWT_SECRET = 'your_secret'"
                exit 1
            }
            
            # Check SSL certificates
            if (-not (Test-Path "deployment\prod\ssl\cert.pem")) {
                Write-Warning "SSL certificates not found. Generating..."
                .\scripts\generate_ssl_certs.ps1
            }
        }
        
        docker-compose -f $composeFile up --build -d
        Write-Success "Services started successfully!"
        
        # Show service URLs
        Write-Host ""
        Write-Success "Access services:"
        switch ($Env) {
            'dev' {
                Write-Host "  - MLflow: http://localhost:5000"
                Write-Host "  - API: http://localhost:8000"
                Write-Host "  - UI: http://localhost:8501"
            }
            'sit' {
                Write-Host "  - MLflow: http://localhost:5001"
                Write-Host "  - API: http://localhost:8001"
                Write-Host "  - UI: http://localhost:8502"
            }
            'uat' {
                Write-Host "  - API: http://localhost/api"
                Write-Host "  - UI: http://localhost/"
                Write-Host "  - MLflow: http://localhost:5002"
            }
            'prod' {
                Write-Host "  - HTTPS: https://localhost/"
                Write-Host "  - Grafana: http://localhost:3000"
                Write-Host "  - Prometheus: http://localhost:9090"
            }
        }
    }
    
    'down' {
        Write-Warning "Stopping services..."
        docker-compose -f $composeFile down
        Write-Success "Services stopped successfully!"
    }
    
    'restart' {
        Write-Warning "Restarting services..."
        docker-compose -f $composeFile restart
        Write-Success "Services restarted successfully!"
    }
    
    'logs' {
        if ($Service) {
            docker-compose -f $composeFile logs -f --tail=100 $Service
        } else {
            docker-compose -f $composeFile logs -f --tail=100
        }
    }
    
    'status' {
        docker-compose -f $composeFile ps
    }
    
    'scale' {
        if ($Env -ne 'prod') {
            Write-Error "Error: Scaling only available for production"
            exit 1
        }
        Write-Warning "Scaling API to $Replicas instances..."
        docker-compose -f $composeFile up --scale api=$Replicas -d
        Write-Success "API scaled successfully!"
    }
    
    'backup' {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "backup_${Env}_$timestamp.sql"
        Write-Warning "Creating database backup: $backupFile"
        
        $dbUser = switch ($Env) {
            'dev' { 'ml_user' }
            'sit' { 'ml_user_sit' }
            'uat' { 'ml_user_uat' }
            'prod' { 'ml_user_prod' }
        }
        
        docker-compose -f $composeFile exec -T postgres pg_dump -U $dbUser ml_evaluation | Out-File -FilePath $backupFile -Encoding utf8
        Write-Success "Backup created: $backupFile"
    }
    
    default {
        Write-Error "Unknown action: $Action"
        exit 1
    }
}
