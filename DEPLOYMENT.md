# KeepShot Deployment Guide

Complete guide for deploying KeepShot to production at **keepshot.xyz**.

---

## 🚀 Quick Deploy (VPS)

### Prerequisites

- Ubuntu 20.04+ or Debian 11+ VPS
- Domain: `api.keepshot.xyz` pointing to your server IP
- Minimum: 2GB RAM, 2 CPU cores, 20GB disk
- Docker & Docker Compose installed

### Step-by-Step Deployment

#### 1. **Setup Server**

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

#### 2. **Configure DNS**

Set up DNS records at your domain registrar:

```
Type: A
Name: api.keepshot.xyz
Value: [Your Server IP]
TTL: 3600
```

Wait 5-10 minutes for DNS propagation. Verify:
```bash
dig api.keepshot.xyz
# or
nslookup api.keepshot.xyz
```

#### 3. **Clone and Configure**

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/keepshot.git
cd keepshot

# Create production environment file
cp .env.production .env

# Edit with your values
nano .env
```

**Important:** Change these values:
- `POSTGRES_PASSWORD` - Strong, unique password
- `OPENAI_API_KEY` - Your OpenAI API key
- `ALLOWED_ORIGINS` - Your frontend domains

#### 4. **Initial SSL Setup**

Before starting the full stack, get SSL certificates:

```bash
# Create required directories
mkdir -p certbot/conf certbot/www

# Start nginx temporarily for certificate generation
docker-compose -f docker-compose.prod.yml up -d nginx

# Get SSL certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d api.keepshot.xyz

# Stop temporary nginx
docker-compose -f docker-compose.prod.yml down
```

#### 5. **Start Production Stack**

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps
```

#### 6. **Run Database Migrations**

```bash
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

#### 7. **Verify Deployment**

```bash
# Health check
curl https://api.keepshot.xyz/health

# Should return:
# {"status":"healthy","version":"1.0.0","service":"keepshot"}

# API docs
open https://api.keepshot.xyz/docs
```

---

## 🔄 SSL Certificate Auto-Renewal

The certbot container automatically renews certificates every 12 hours. Verify renewal works:

```bash
# Test renewal
docker-compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f db
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### System Resources

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Database

```bash
# PostgreSQL shell
docker-compose -f docker-compose.prod.yml exec db psql -U keepshot_prod -d keepshot_prod

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U keepshot_prod keepshot_prod > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U keepshot_prod keepshot_prod
```

---

## 🔒 Security Checklist

- ✅ Strong PostgreSQL password set
- ✅ SSL/HTTPS enabled with Let's Encrypt
- ✅ DEBUG=false in production
- ✅ CORS configured for specific domains
- ✅ Rate limiting enabled in Nginx
- ✅ Regular database backups configured
- ✅ Firewall configured (UFW or cloud firewall)
- ✅ SSH key authentication (disable password auth)
- ✅ Fail2ban installed (optional but recommended)

### Setup Firewall

```bash
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
cd /opt/keepshot

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build app
docker-compose -f docker-compose.prod.yml up -d app

# Run any new migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Update Dependencies

```bash
# Rebuild with no cache
docker-compose -f docker-compose.prod.yml build --no-cache app
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🌐 Alternative Deployment Options

### Railway.app

1. **Connect Repository**
   - Go to [Railway.app](https://railway.app)
   - Create new project from GitHub repo

2. **Configure**
   - Add PostgreSQL service
   - Add environment variables from `.env.production`

3. **Deploy**
   - Railway automatically deploys
   - Get provided URL or add custom domain `api.keepshot.xyz`

### Render.com

1. **Create Web Service**
   - Connect GitHub repository
   - Select Docker as runtime

2. **Configure**
   - Add PostgreSQL database
   - Set environment variables
   - Add custom domain `api.keepshot.xyz`

3. **Deploy**
   - Automatic SSL included
   - Auto-deploy on git push

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Launch app
fly launch

# Set secrets
fly secrets set OPENAI_API_KEY=sk-...
fly secrets set POSTGRES_PASSWORD=...

# Deploy
fly deploy

# Add domain
fly certs add api.keepshot.xyz
```

---

## 🐛 Troubleshooting

### App won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Common issues:
# - Database not ready: Wait for healthcheck
# - Missing env vars: Check .env file
# - Port conflict: Check if port 8000 is available
```

### SSL certificate issues

```bash
# Check nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Regenerate certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --force-renewal \
  -d api.keepshot.xyz
```

### Database connection errors

```bash
# Check if database is running
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Test connection
docker-compose -f docker-compose.prod.yml exec app python -c "from app.database import engine; engine.connect()"
```

### WebSocket not connecting

- Ensure nginx WebSocket config is correct
- Check CORS settings allow your frontend domain
- Verify SSL certificate is valid for wss:// connections

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# In docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3  # Run 3 instances
```

Add load balancer (Nginx, HAProxy, or cloud LB)

### Vertical Scaling

Upgrade VPS resources:
- 4GB RAM + 4 CPU cores (recommended for production)
- 8GB RAM + 8 CPU cores (for high traffic)

### Database Scaling

Use managed PostgreSQL:
- AWS RDS
- Google Cloud SQL
- DigitalOcean Managed Databases
- Supabase

Update `DATABASE_URL` in `.env`

---

## 🎯 Performance Optimization

### 1. **Enable Redis Caching** (Optional)

Add Redis to `docker-compose.prod.yml`:

```yaml
redis:
  image: redis:alpine
  restart: always
```

### 2. **Optimize Database**

```sql
-- Create indexes
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_snapshots_bookmark_id ON snapshots(bookmark_id);
```

### 3. **CDN for Static Assets**

Use CloudFlare or AWS CloudFront for:
- Faster global delivery
- DDoS protection
- Additional caching layer

---

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Review [Troubleshooting](#-troubleshooting)
3. Open GitHub issue with logs

---

**Deployed at:** https://api.keepshot.xyz 🚀
