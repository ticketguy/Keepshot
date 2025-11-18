#!/bin/bash

# Quick fix script for SSL-related restart loops
# Run this on the droplet to fix the current issue

set -e

INSTALL_DIR="/opt/keepshot"
cd $INSTALL_DIR

echo "🔧 Fixing SSL restart loop..."
echo ""

# Step 1: Stop all containers
echo "1️⃣  Stopping containers..."
docker compose -f docker-compose.prod.yml down

# Step 2: Backup SSL config and use init config
echo ""
echo "2️⃣  Switching to HTTP-only configuration..."
if [ -f nginx/conf.d/api.keepshot.xyz.conf ]; then
    mv nginx/conf.d/api.keepshot.xyz.conf nginx/conf.d/api.keepshot.xyz.conf.ssl
    echo "   ✅ Backed up SSL configuration"
fi

if [ -f nginx/conf.d/api.keepshot.xyz.init.conf ]; then
    cp nginx/conf.d/api.keepshot.xyz.init.conf nginx/conf.d/api.keepshot.xyz.conf
    echo "   ✅ Using HTTP-only configuration"
fi

# Step 3: Start containers with HTTP-only config
echo ""
echo "3️⃣  Starting containers..."
docker compose -f docker-compose.prod.yml up -d

# Step 4: Wait for services to be healthy
echo ""
echo "4️⃣  Waiting for services to start..."
sleep 20

# Step 5: Run migrations
echo ""
echo "5️⃣  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head || {
    echo "   ⚠️  Migrations might have failed. Check logs:"
    echo "   docker compose -f docker-compose.prod.yml logs app"
}

# Step 6: Check if containers are running
echo ""
echo "6️⃣  Checking container status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Containers should now be running!"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  Verify the API is accessible:"
echo "   curl http://api.keepshot.xyz/health"
echo ""
echo "2️⃣  Get SSL certificate (you'll need your email):"
echo "   docker compose -f docker-compose.prod.yml run --rm certbot certonly \\"
echo "     --webroot --webroot-path=/var/www/certbot \\"
echo "     --email YOUR_EMAIL --agree-tos --no-eff-email \\"
echo "     -d api.keepshot.xyz"
echo ""
echo "3️⃣  Switch to HTTPS configuration:"
echo "   ./switch-to-https.sh"
echo ""
echo "4️⃣  Add your OpenAI API key:"
echo "   nano .env"
echo "   (Find OPENAI_API_KEY and add your key)"
echo "   docker compose -f docker-compose.prod.yml restart app"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
