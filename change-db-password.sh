#!/bin/bash
# Change the keepshot database password on the prod server.
# Updates both PostgreSQL and the .env file, then restarts the app.
set -e

if [ -z "$1" ]; then
    echo "Usage: bash change-db-password.sh <new-password>"
    exit 1
fi

NEW_PASS="$1"
ENV_FILE="$(dirname "$0")/.env"

# 1. Update PostgreSQL
echo "Updating PostgreSQL password..."
su -c "psql -c \"ALTER USER keepshot WITH PASSWORD '$NEW_PASS';\"" postgres

# 2. Update DATABASE_URL in .env
echo "Updating .env..."
# Replace the password portion in DATABASE_URL (handles any current password)
sed -i "s|postgresql://keepshot:[^@]*@|postgresql://keepshot:$NEW_PASS@|g" "$ENV_FILE"

echo "Done. New DATABASE_URL:"
grep DATABASE_URL "$ENV_FILE"

# 3. Restart app if supervisor is managing it
if supervisorctl status keepshot-app &>/dev/null; then
    echo "Restarting app..."
    supervisorctl restart keepshot-app
    echo "App restarted."
fi

echo ""
echo "Password changed successfully."
