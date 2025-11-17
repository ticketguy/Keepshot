#!/bin/bash

# Script to switch from HTTP-only to HTTPS configuration
# Run this AFTER SSL certificates have been obtained

set -e

INSTALL_DIR="/opt/keepshot"
cd $INSTALL_DIR

echo "🔄 Switching to HTTPS configuration..."

# Backup init config
if [ -f nginx/conf.d/api.keepshot.xyz.init.conf ]; then
    mv nginx/conf.d/api.keepshot.xyz.init.conf nginx/conf.d/api.keepshot.xyz.init.conf.bak
    echo "✅ Backed up init configuration"
fi

# Ensure the HTTPS config is in place
if [ ! -f nginx/conf.d/api.keepshot.xyz.conf ]; then
    echo "❌ HTTPS configuration not found!"
    exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx..."
docker compose -f docker-compose.prod.yml restart nginx

echo "✅ Switched to HTTPS configuration"
echo ""
echo "Verify HTTPS is working:"
echo "  curl https://api.keepshot.xyz/health"
