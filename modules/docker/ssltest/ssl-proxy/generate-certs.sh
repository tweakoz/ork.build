#!/bin/bash

set -e

echo "🔐 Generating SSL certificates for stunnel..."

# Generate private key
openssl genrsa -out /etc/stunnel/server.key 2048

# Generate certificate signing request
openssl req -new -key /etc/stunnel/server.key -out /etc/stunnel/server.csr -subj "/C=US/ST=CA/L=SF/O=Example/OU=IT/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in /etc/stunnel/server.csr -signkey /etc/stunnel/server.key -out /etc/stunnel/server.crt

# Create combined PEM file (certificate + private key)
cat /etc/stunnel/server.crt /etc/stunnel/server.key > /etc/stunnel/server.pem

# Set permissions
chmod 600 /etc/stunnel/server.pem
chmod 600 /etc/stunnel/server.key
chmod 644 /etc/stunnel/server.crt

# Clean up temporary CSR
rm /etc/stunnel/server.csr

echo "✅ SSL certificates generated:"
echo "   Combined PEM: /etc/stunnel/server.pem"
echo "   Certificate: /etc/stunnel/server.crt" 
echo "   Private Key: /etc/stunnel/server.key" 