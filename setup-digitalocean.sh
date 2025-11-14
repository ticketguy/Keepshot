#!/bin/bash

# KeepShot DigitalOcean Deployment Script
# For deploying to api.keepshot.xyz

set -e

echo "🌊 KeepShot DigitalOcean Setup"
echo "=============================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (you should be by default on DigitalOcean)"
    exit 1
fi

# Configuration
DOMAIN="api.keepshot.xyz"
EMAIL=""  # Will prompt user
REPO_URL="https://github.com/ticketguy/Keepshot.git"
BRANCH="claude/learn-and-update-01LyYHSBzEmXj5iKwj5nqU3e"
INSTALL_DIR="/opt/keepshot"

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Install Dir: $INSTALL_DIR"
echo ""

# Get email for SSL certificate
read -p "Enter your email for SSL certificate: " EMAIL
if [ -z "$EMAIL" ]; then
    echo "❌ Email is required for SSL certificate"
    exit 1
fi

echo ""
echo "Will deploy to: https://$DOMAIN"
echo "SSL notifications to: $EMAIL"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "1️⃣  Updating system..."
apt update && apt upgrade -y

echo ""
echo "2️⃣  Installing essential packages..."
apt install -y curl git ufw

echo ""
echo "3️⃣  Installing Docker..."
if ! command -v docker &> /dev/null; then
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
if ! docker compose version &> /dev/null; then
    apt install -y docker-compose-plugin
else
    echo "   ✅ Docker Compose already installed"
fi

echo ""
echo "5️⃣  Configuring firewall..."
# Configure UFW
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw status

echo ""
echo "6️⃣  Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "   ⚠️  Directory exists, pulling latest..."
    cd $INSTALL_DIR
    git pull origin $BRANCH
else
    git clone -b $BRANCH $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

echo ""
echo "7️⃣  Creating environment file..."
if [ ! -f .env ]; then
    cp .env.production .env

    # Generate secure password
    PG_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

    # Update .env with generated password
    sed -i "s/CHANGE_THIS_SECURE_PASSWORD/$PG_PASSWORD/g" .env

    echo ""
    echo "   ✅ Created .env with secure database password"
    echo "   ⚠️  IMPORTANT: You still need to add your OPENAI_API_KEY!"
    echo ""
else
    echo "   ✅ .env already exists"
fi

echo ""
echo "8️⃣  Creating required directories..."
mkdir -p certbot/conf certbot/www nginx/conf.d storage logs

# Ensure proper permissions
chmod -R 755 nginx
chmod +x setup-production.sh

echo ""
echo "9️⃣  Getting SSL certificate..."
echo "   Starting nginx for certificate verification..."

# Start nginx temporarily
docker compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to start
sleep 10

# Get certificate
echo "   Requesting SSL certificate from Let's Encrypt..."
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d $DOMAIN || {
        echo "❌ SSL certificate generation failed!"
        echo "   This might be because:"
        echo "   1. DNS is not propagated yet (wait 5-10 minutes)"
        echo "   2. Domain doesn't point to this server"
        echo "   3. Port 80 is not accessible"
        echo ""
        echo "   You can retry manually with:"
        echo "   cd $INSTALL_DIR"
        echo "   docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email $EMAIL --agree-tos --no-eff-email -d $DOMAIN"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }

# Stop temporary nginx
docker compose -f docker-compose.prod.yml down

echo ""
echo "🔟 Starting production stack..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "1️⃣1️⃣  Waiting for services to start..."
sleep 15

echo ""
echo "1️⃣2️⃣  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head || {
    echo "   ⚠️  Migrations might have failed. Check logs:"
    echo "   docker compose -f docker-compose.prod.yml logs app"
}

echo ""
echo "1️⃣3️⃣  Setting up automatic updates..."
# Create update script
cat > /usr/local/bin/keepshot-update.sh << 'UPDATEEOF'
#!/bin/bash
cd /opt/keepshot
git pull
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head
UPDATEEOF

chmod +x /usr/local/bin/keepshot-update.sh

echo ""
echo "✅ KeepShot deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Your API is deployed at: https://$DOMAIN"
echo ""
echo "📋 IMPORTANT NEXT STEPS:"
echo ""
echo "1️⃣  Add your OpenAI API key:"
echo "   nano $INSTALL_DIR/.env"
echo "   (Find OPENAI_API_KEY and add your key)"
echo ""
echo "2️⃣  Restart the app:"
echo "   cd $INSTALL_DIR"
echo "   docker compose -f docker-compose.prod.yml restart app"
echo ""
echo "3️⃣  Verify deployment:"
echo "   curl https://$DOMAIN/health"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 USEFUL COMMANDS:"
echo ""
echo "View logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "Restart services:"
echo "  docker compose -f docker-compose.prod.yml restart"
echo ""
echo "Update KeepShot:"
echo "  /usr/local/bin/keepshot-update.sh"
echo ""
echo "Database backup:"
echo "  docker compose -f docker-compose.prod.yml exec db pg_dump -U keepshot_prod keepshot_prod > backup.sql"
echo ""
echo "Monitor resources:"
echo "  docker stats"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 Full documentation:"
echo "   - README.md: $INSTALL_DIR/README.md"
echo "   - Deployment guide: $INSTALL_DIR/DEPLOYMENT.md"
echo "   - API docs: https://$DOMAIN/docs"
echo ""
echo "🔐 Database password saved in: $INSTALL_DIR/.env"
echo ""
echo "Happy deploying! 🚀"
