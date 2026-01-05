#!/bin/bash
# Generate self-signed SSL certificates for local testing
# For production, use proper CA-signed certificates

set -e

CERT_DIR="./deployment/prod/ssl"
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificates for production environment..."

# Generate private key
openssl genrsa -out "$CERT_DIR/key.pem" 2048

# Generate certificate signing request
openssl req -new -key "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.csr" \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in "$CERT_DIR/cert.csr" \
    -signkey "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem"

# Clean up CSR
rm "$CERT_DIR/cert.csr"

echo "SSL certificates generated successfully!"
echo "Location: $CERT_DIR"
echo ""
echo "IMPORTANT: These are self-signed certificates for testing only."
echo "For production deployment, use certificates from a trusted CA."
