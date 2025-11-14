#!/bin/bash

# KeepShot Production Setup Script for keepshot.xyz
# This script automates the deployment process on a fresh Ubuntu/Debian VPS

set -e  # Exit on any error

echo "🚀 KeepShot Production Setup"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Configuration
DOMAIN="api.keepshot.xyz"
EMAIL="your-email@example.com"  # Change this!
INSTALL_DIR="/opt/keepshot"

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo "   Install Dir: $INSTALL_DIR"
echo ""

read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "1️⃣  Updating system..."
apt update && apt upgrade -y

echo ""
echo "2️⃣  Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "   ✅ Docker already installed"
fi

echo ""
echo "3️⃣  Installing Docker Compose..."
if ! docker compose version &> /dev/null; then
    apt install docker-compose-plugin -y
else
    echo "   ✅ Docker Compose already installed"
fi

echo ""
echo "4️⃣  Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "   ⚠️  Directory exists, pulling latest..."
    cd $INSTALL_DIR
    git pull
else
    git clone https://github.com/yourusername/keepshot.git $INSTALL_DIR
    cd $INSTALL_DIR
fi

echo ""
echo "5️⃣  Creating environment file..."
if [ ! -f .env ]; then
    cp .env.production .env

    # Generate secure password
    PG_PASSWORD=$(openssl rand -base64 32)

    # Update .env
    sed -i "s/CHANGE_THIS_SECURE_PASSWORD/$PG_PASSWORD/g" .env

    echo "   ⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo "   File location: $INSTALL_DIR/.env"
else
    echo "   ✅ .env already exists"
fi

echo ""
echo "6️⃣  Setting up directories..."
mkdir -p certbot/conf certbot/www nginx/conf.d storage logs

echo ""
echo "7️⃣  Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "y" | ufw enable || true
    ufw status
else
    echo "   ⚠️  UFW not installed, skipping firewall setup"
fi

echo ""
echo "8️⃣  Getting SSL certificate..."
# Start nginx for certificate
docker compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to start
sleep 5

# Get certificate
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Stop nginx
docker compose -f docker-compose.prod.yml down

echo ""
echo "9️⃣  Starting production stack..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "🔟 Waiting for services to start..."
sleep 10

echo ""
echo "1️⃣1️⃣  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env and add your OPENAI_API_KEY:"
echo "      nano $INSTALL_DIR/.env"
echo ""
echo "   2. Restart the stack:"
echo "      cd $INSTALL_DIR"
echo "      docker compose -f docker-compose.prod.yml restart app"
echo ""
echo "   3. Verify deployment:"
echo "      curl https://$DOMAIN/health"
echo ""
echo "   4. View API docs:"
echo "      https://$DOMAIN/docs"
echo ""
echo "📊 Useful commands:"
echo "   View logs:    docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart:      docker compose -f docker-compose.prod.yml restart"
echo "   Stop:         docker compose -f docker-compose.prod.yml down"
echo "   Update:       git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "🎉 KeepShot is now running at https://$DOMAIN"
