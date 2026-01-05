# Generate self-signed SSL certificates for local testing
# For production, use proper CA-signed certificates

$ErrorActionPreference = "Stop"

$certDir = ".\deployment\prod\ssl"
New-Item -ItemType Directory -Force -Path $certDir | Out-Null

Write-Host "Generating self-signed SSL certificates for production environment..." -ForegroundColor Green

# Check if OpenSSL is available
$opensslPath = (Get-Command openssl -ErrorAction SilentlyContinue).Source

if (-not $opensslPath) {
    Write-Host "OpenSSL not found. Attempting to use Windows certificate generation..." -ForegroundColor Yellow
    
    # Alternative: Use Windows built-in certificate generation
    $cert = New-SelfSignedCertificate `
        -DnsName "localhost" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyAlgorithm RSA `
        -KeyLength 2048 `
        -NotAfter (Get-Date).AddDays(365)
    
    # Export certificate and private key
    $password = ConvertTo-SecureString -String "temp123" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "$certDir\cert.pfx" -Password $password
    
    Write-Host "SSL certificate generated using Windows certificate store!" -ForegroundColor Green
    Write-Host "Location: $certDir\cert.pfx" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To convert PFX to PEM format for Nginx, use:" -ForegroundColor Yellow
    Write-Host "  openssl pkcs12 -in cert.pfx -out cert.pem -nodes" -ForegroundColor Gray
} else {
    Write-Host "Using OpenSSL: $opensslPath" -ForegroundColor Cyan
    
    # Generate private key
    & openssl genrsa -out "$certDir\key.pem" 2048
    
    # Generate certificate signing request
    & openssl req -new -key "$certDir\key.pem" -out "$certDir\cert.csr" `
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    # Generate self-signed certificate (valid for 365 days)
    & openssl x509 -req -days 365 -in "$certDir\cert.csr" `
        -signkey "$certDir\key.pem" -out "$certDir\cert.pem"
    
    # Clean up CSR
    Remove-Item "$certDir\cert.csr" -Force
    
    Write-Host "SSL certificates generated successfully!" -ForegroundColor Green
    Write-Host "Location: $certDir" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "IMPORTANT: These are self-signed certificates for testing only." -ForegroundColor Red
Write-Host "For production deployment, use certificates from a trusted CA." -ForegroundColor Red
