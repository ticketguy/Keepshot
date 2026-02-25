#!/bin/bash

# KeepShot Frontend Deployment Script
# Builds the React frontend and provisions SSL for keepshot.xyz
# Run this on the DigitalOcean droplet after: git pull

set -e

DOMAIN="keepshot.xyz"
EMAIL="${CERTBOT_EMAIL:-your-email@example.com}"  # Override: CERTBOT_EMAIL=you@example.com ./deploy-frontend.sh
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_DIR="$INSTALL_DIR/nginx/conf.d"
CERT_PATH="$INSTALL_DIR/certbot/conf/live/$DOMAIN/fullchain.pem"
HTTPS_CONF="$CONF_DIR/keepshot.xyz.conf"
HTTPS_CONF_BAK="$CONF_DIR/keepshot.xyz.conf.bak"

echo "=== KeepShot Frontend Deployment ==="
echo "Domain : $DOMAIN"
echo "Dir    : $INSTALL_DIR"
echo ""

cd "$INSTALL_DIR"

# ── 1. Build the React frontend ─────────────────────────────────────────────
echo "1/4  Building React frontend..."

if ! command -v node &>/dev/null; then
    echo "  Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

cd frontend
npm ci --prefer-offline
npm run build
cd ..

echo "  ✓ Build complete → frontend/dist/"
echo ""

# ── 2. Obtain SSL certificate for keepshot.xyz (if needed) ──────────────────
echo "2/4  Checking SSL certificate for $DOMAIN..."

if [ ! -f "$CERT_PATH" ]; then
    echo "  Certificate not found. Obtaining from Let's Encrypt..."

    # Temporarily disable the HTTPS nginx config (requires cert to load)
    if [ -f "$HTTPS_CONF" ]; then
        mv "$HTTPS_CONF" "$HTTPS_CONF_BAK"
        echo "  (temporarily disabled keepshot.xyz.conf during cert acquisition)"
    fi

    # Reload/start nginx without the HTTPS config (HTTP-only init config active)
    if docker compose -f docker-compose.prod.yml ps nginx 2>/dev/null | grep -q "Up"; then
        docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
    else
        docker compose -f docker-compose.prod.yml up -d nginx
        sleep 5
    fi

    # Get the certificate
    docker compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"

    # Re-enable the HTTPS config now that the cert exists
    if [ -f "$HTTPS_CONF_BAK" ]; then
        mv "$HTTPS_CONF_BAK" "$HTTPS_CONF"
        echo "  ✓ Certificate obtained — HTTPS config re-enabled"
    fi
else
    echo "  ✓ Certificate already exists (auto-renews via certbot container)"
fi

echo ""

# ── 3. Reload nginx to pick up new frontend files + HTTPS config ─────────────
echo "3/4  Reloading nginx..."

if docker compose -f docker-compose.prod.yml ps nginx 2>/dev/null | grep -q "Up"; then
    docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
    echo "  ✓ Nginx reloaded"
else
    docker compose -f docker-compose.prod.yml up -d
    echo "  ✓ Stack started"
fi

echo ""

# ── 4. Verify ────────────────────────────────────────────────────────────────
echo "4/4  Verifying..."
sleep 3

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ https://$DOMAIN/ → HTTP $HTTP_CODE"
else
    echo "  ⚠  https://$DOMAIN/ returned HTTP $HTTP_CODE"
    echo "     (Check logs: docker compose -f docker-compose.prod.yml logs nginx)"
fi

echo ""
echo "=== Done ==="
echo ""
echo "  Frontend : https://$DOMAIN"
echo "  API      : https://api.$DOMAIN"
echo ""
echo "To redeploy after a code change:"
echo "  git pull && ./deploy-frontend.sh"
