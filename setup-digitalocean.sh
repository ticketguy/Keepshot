#!/bin/bash

# KeepShot DigitalOcean Deployment Script
# Single script — deploys backend (api.keepshot.xyz) + frontend (keepshot.xyz)
# Run as root on a fresh Ubuntu/Debian droplet

set -e

echo "🌊 KeepShot DigitalOcean Setup"
echo "=============================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (you should be by default on DigitalOcean)"
    exit 1
fi

# ── Configuration ────────────────────────────────────────────────────────────
API_DOMAIN="api.keepshot.xyz"
FRONTEND_DOMAIN="keepshot.xyz"
REPO_URL="https://github.com/ticketguy/Keepshot.git"
BRANCH="main"
INSTALL_DIR="/opt/keepshot"

echo "📋 Configuration:"
echo "   Backend  : https://$API_DOMAIN"
echo "   Frontend : https://$FRONTEND_DOMAIN"
echo "   Install  : $INSTALL_DIR"
echo ""

read -p "Enter your email for SSL certificates: " EMAIL
if [ -z "$EMAIL" ]; then
    echo "❌ Email is required for SSL certificates"
    exit 1
fi

echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# ── 1. System packages ────────────────────────────────────────────────────────
echo ""
echo "1️⃣  Updating system..."
apt update && apt upgrade -y
apt install -y curl git ufw

# ── 2. Node.js (for frontend build) ──────────────────────────────────────────
echo ""
echo "2️⃣  Installing Node.js 20..."
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
else
    echo "   ✅ Node.js already installed ($(node --version))"
fi

# ── 3. Docker ─────────────────────────────────────────────────────────────────
echo ""
echo "3️⃣  Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "   ✅ Docker already installed"
fi

echo ""
echo "4️⃣  Installing Docker Compose..."
if ! docker compose version &>/dev/null; then
    apt install -y docker-compose-plugin
else
    echo "   ✅ Docker Compose already installed"
fi

# ── 4. Firewall ───────────────────────────────────────────────────────────────
echo ""
echo "5️⃣  Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw status

# ── 5. Clone repo ─────────────────────────────────────────────────────────────
echo ""
echo "6️⃣  Cloning repository ($BRANCH)..."
if [ -d "$INSTALL_DIR" ]; then
    echo "   Directory exists, pulling latest..."
    cd $INSTALL_DIR
    git pull origin $BRANCH
else
    git clone -b $BRANCH $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

# ── 6. Environment file ───────────────────────────────────────────────────────
echo ""
echo "7️⃣  Creating environment file..."
if [ ! -f .env ]; then
    cp .env.production .env
    PG_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    sed -i "s/CHANGE_THIS_SECURE_PASSWORD/$PG_PASSWORD/g" .env
    echo "   ✅ Created .env with secure database password"
    echo "   ⚠️  You still need to add your OPENAI_API_KEY!"
else
    echo "   ✅ .env already exists"
fi

# ── 7. Directories ────────────────────────────────────────────────────────────
echo ""
echo "8️⃣  Creating required directories..."
mkdir -p certbot/conf certbot/www nginx/conf.d storage logs
chmod -R 755 nginx

# ── 8. Build the React frontend ───────────────────────────────────────────────
echo ""
echo "9️⃣  Building React frontend..."
cd frontend
npm ci --prefer-offline
npm run build
cd ..
echo "   ✅ Frontend built → frontend/dist/"

# ── 9. Bootstrap nginx + SSL for api.keepshot.xyz ────────────────────────────
echo ""
echo "🔟 Getting SSL certificate for $API_DOMAIN..."

# Use HTTP-only nginx config so certbot can reach /.well-known/acme-challenge/
if [ -f nginx/conf.d/api.keepshot.xyz.conf ]; then
    mv nginx/conf.d/api.keepshot.xyz.conf nginx/conf.d/api.keepshot.xyz.conf.ssl
fi
if [ -f nginx/conf.d/keepshot.xyz.conf ]; then
    mv nginx/conf.d/keepshot.xyz.conf nginx/conf.d/keepshot.xyz.conf.ssl
fi

# Start nginx with HTTP-only configs
docker compose -f docker-compose.prod.yml up -d nginx
sleep 8

docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$API_DOMAIN" || {
        echo "   ⚠️  SSL for $API_DOMAIN failed. Check DNS propagation and retry."
        echo "   Re-run after fixing: ./setup-digitalocean.sh"
        exit 1
    }

echo "   ✅ SSL obtained for $API_DOMAIN"

# ── 10. SSL for keepshot.xyz ──────────────────────────────────────────────────
echo ""
echo "1️⃣1️⃣  Getting SSL certificate for $FRONTEND_DOMAIN..."

docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$FRONTEND_DOMAIN" \
    -d "www.$FRONTEND_DOMAIN" || {
        echo "   ⚠️  SSL for $FRONTEND_DOMAIN failed. Check DNS propagation and retry."
        echo "   Re-run after fixing: ./setup-digitalocean.sh"
        exit 1
    }

echo "   ✅ SSL obtained for $FRONTEND_DOMAIN"

# ── 11. Restore HTTPS nginx configs + start full stack ───────────────────────
echo ""
echo "1️⃣2️⃣  Switching to HTTPS configuration..."

[ -f nginx/conf.d/api.keepshot.xyz.conf.ssl ] && \
    mv nginx/conf.d/api.keepshot.xyz.conf.ssl nginx/conf.d/api.keepshot.xyz.conf

[ -f nginx/conf.d/keepshot.xyz.conf.ssl ] && \
    mv nginx/conf.d/keepshot.xyz.conf.ssl nginx/conf.d/keepshot.xyz.conf

docker compose -f docker-compose.prod.yml down

echo ""
echo "1️⃣3️⃣  Starting full production stack..."
docker compose -f docker-compose.prod.yml up -d
sleep 15

# ── 12. Database migrations ───────────────────────────────────────────────────
echo ""
echo "1️⃣4️⃣  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head || {
    echo "   ⚠️  Migrations failed. Check: docker compose -f docker-compose.prod.yml logs app"
}

# ── 13. Auto-update script ────────────────────────────────────────────────────
cat > /usr/local/bin/keepshot-update.sh << 'UPDATEEOF'
#!/bin/bash
set -e
cd /opt/keepshot
git pull
cd frontend && npm ci --prefer-offline && npm run build && cd ..
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
echo "✅ Update complete"
UPDATEEOF
chmod +x /usr/local/bin/keepshot-update.sh

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "✅ KeepShot deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Frontend : https://$FRONTEND_DOMAIN"
echo "   API      : https://$API_DOMAIN"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  IMPORTANT — Add your OpenAI API key:"
echo "   nano $INSTALL_DIR/.env"
echo "   (set OPENAI_API_KEY=sk-...)"
echo ""
echo "   Then restart the app:"
echo "   docker compose -f docker-compose.prod.yml restart app"
echo ""
echo "📊 Useful commands:"
echo "   Logs    : docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart : docker compose -f docker-compose.prod.yml restart"
echo "   Update  : /usr/local/bin/keepshot-update.sh"
echo "   Health  : curl https://$API_DOMAIN/health"
echo ""
