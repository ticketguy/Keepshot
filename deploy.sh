#!/bin/bash
# Manual deploy script — same steps as CI/CD
set -e

cd "$(dirname "$0")"

echo "Pulling latest code..."
git pull origin main

echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo "Running migrations..."
python3 -m alembic upgrade head

echo "Restarting app..."
supervisorctl restart keepshot-app

sleep 3
echo "Health check..."
curl -sf http://localhost:8000/health
echo ""
echo "Deploy complete."
