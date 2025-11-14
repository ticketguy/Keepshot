# KeepShot

**AI-Powered Bookmark Monitoring System**

KeepShot is a production-ready, lightweight backend for monitoring bookmarks and detecting changes using AI. Built with FastAPI, PostgreSQL, and OpenAI, it's designed to be **auth-agnostic**, **multi-content**, and **plug-and-play** via Docker.

---

## 🎯 Features

- **Multi-Content Support**: URLs, images, videos, PDFs, and text snippets
- **AI-Powered Monitoring**: Intelligent watchpoint extraction and change detection
- **Real-Time Notifications**: WebSocket-based push notifications
- **Auth-Agnostic**: Bring your own authentication (JWT, OAuth, Portid, API keys, etc.)
- **Lightweight**: No Redis/Celery overhead - uses APScheduler
- **Dockerized**: One command to run the entire stack
- **REST API**: Clean, well-documented API with OpenAPI/Swagger
- **Scalable**: Efficient background monitoring with configurable intervals
- **Smart Detection**: AI determines what changes are significant

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd keepshot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Start the stack**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**

   **Local Development:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

   **Production (keepshot.xyz):**
   - API: https://api.keepshot.xyz
   - Docs: https://api.keepshot.xyz/docs
   - Health: https://api.keepshot.xyz/health

That's it! KeepShot is now running.

---

## 📚 API Documentation

### Authentication

KeepShot is **auth-agnostic**. For development, send user ID in header:

```bash
# Local Development
curl -H "X-User-Id: user123" http://localhost:8000/api/v1/bookmarks

# Production
curl -H "X-User-Id: user123" https://api.keepshot.xyz/api/v1/bookmarks
```

For production, implement your own auth middleware (see `app/dependencies.py`).

### Endpoints

#### Bookmarks

**Create Bookmark**
```bash
POST /api/v1/bookmarks
Content-Type: application/json
X-User-Id: user123

{
  "content_type": "url",
  "url": "https://example.com/article",
  "title": "Interesting Article",
  "monitoring_enabled": true,
  "check_interval": 60
}
```

**List Bookmarks**
```bash
GET /api/v1/bookmarks?page=1&page_size=20
X-User-Id: user123
```

**Get Bookmark**
```bash
GET /api/v1/bookmarks/{bookmark_id}
X-User-Id: user123
```

**Update Bookmark**
```bash
PATCH /api/v1/bookmarks/{bookmark_id}
Content-Type: application/json
X-User-Id: user123

{
  "monitoring_enabled": false,
  "check_interval": 120
}
```

**Delete Bookmark**
```bash
DELETE /api/v1/bookmarks/{bookmark_id}
X-User-Id: user123
```

**Trigger Immediate Check**
```bash
POST /api/v1/bookmarks/{bookmark_id}/check
X-User-Id: user123
```

**Get History**
```bash
GET /api/v1/bookmarks/{bookmark_id}/history
X-User-Id: user123
```

#### Notifications

**List Notifications**
```bash
GET /api/v1/notifications?read=false
X-User-Id: user123
```

**Get Notification**
```bash
GET /api/v1/notifications/{notification_id}
X-User-Id: user123
```

**Mark as Read**
```bash
PATCH /api/v1/notifications/{notification_id}
Content-Type: application/json
X-User-Id: user123

{
  "read": true
}
```

**Mark All Read**
```bash
POST /api/v1/notifications/mark-all-read
X-User-Id: user123
```

**Delete Notification**
```bash
DELETE /api/v1/notifications/{notification_id}
X-User-Id: user123
```

### WebSocket

**Connect for Real-Time Notifications**

```javascript
// Local Development
const ws = new WebSocket('ws://localhost:8000/ws/user123');

// Production
const ws = new WebSocket('wss://api.keepshot.xyz/ws/user123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Notification:', data);
};
```

Message format:
```json
{
  "type": "notification",
  "data": {
    "id": "notif-id",
    "bookmark_id": "bookmark-id",
    "notification_type": "change",
    "title": "Price Drop Detected!",
    "message": "The price dropped from $99 to $79",
    "created_at": "2024-01-01T00:00:00Z",
    "read": false
  }
}
```

---

## 🏗️ Architecture

### Tech Stack

- **FastAPI**: Modern async web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: ORM for database operations
- **OpenAI**: AI-powered content analysis
- **Playwright**: JavaScript-capable web scraping
- **APScheduler**: Background task scheduling
- **WebSockets**: Real-time notifications

### Content Types

| Type | Description | What's Monitored |
|------|-------------|------------------|
| `url` | Web pages, articles, products | Content, metadata, key fields |
| `image` | Images, screenshots | Metadata, visual content |
| `video` | YouTube, TikTok, etc. | Title, views, likes, description |
| `pdf` | Documents, papers | Text content, metadata |
| `text` | Text snippets, notes | Raw text |

### How It Works

1. **Bookmark Created** → Content scraped and stored
2. **AI Extracts Watchpoints** → Identifies key fields to monitor
3. **Scheduler Checks Periodically** → Based on configured interval
4. **Change Detected** → Compares new snapshot with previous
5. **AI Analyzes Significance** → Scores importance (0.0-1.0)
6. **Notification Generated** → If significant (≥0.5)
7. **Push via WebSocket** → Real-time notification to user

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/keepshot

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Monitoring
DEFAULT_CHECK_INTERVAL=60  # minutes
MAX_CONCURRENT_CHECKS=10

# Storage
STORAGE_PATH=/app/storage
MAX_FILE_SIZE=100  # MB
```

### Monitoring Intervals

- **5 min**: Highly volatile (stock prices, sports scores)
- **60 min**: Normal (news, products, social posts)
- **720 min (12h)**: Low-priority (articles, static content)
- **1440 min (24h)**: Rare changes (documentation, PDFs)

---

## 🔐 Authentication Integration

KeepShot is **auth-agnostic**. Implement your own authentication middleware:

### Example: JWT

```python
# app/dependencies.py

from fastapi import Header, HTTPException
import jwt

async def get_current_user_id(
    authorization: str = Header(None)
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(401, "Invalid token")
```

### Example: Portid

```python
from harboria_portid import PortIDClient

portid = PortIDClient(app_id="your-app-id", sync_server_url="...")

async def get_current_user_id(
    x_portid_token: str = Header(None)
) -> str:
    try:
        user_data = await portid.verify_token(x_portid_token)
        return user_data["user_id"]
    except:
        raise HTTPException(401, "Invalid Portid token")
```

### Example: API Key

```python
async def get_current_user_id(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db)
) -> str:
    user = db.query(User).filter_by(api_key=x_api_key).first()
    if not user:
        raise HTTPException(401, "Invalid API key")
    return user.id
```

---

## 🧪 Development

### Manual Setup (without Docker)

1. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Setup database**
   ```bash
   # Start PostgreSQL
   # Update DATABASE_URL in .env

   # Run migrations
   alembic upgrade head
   ```

3. **Run server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
pytest tests/
```

---

## 📦 Deployment

### Local Development

```bash
docker-compose up -d
```

### Production Deployment (keepshot.xyz)

#### Option 1: VPS with Docker Compose + Nginx (Recommended)

1. **Setup DNS**
   ```
   A Record: api.keepshot.xyz → [Your Server IP]
   ```

2. **Clone and Configure**
   ```bash
   git clone https://github.com/yourusername/keepshot.git
   cd keepshot
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Deploy with SSL**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

This includes:
- Nginx reverse proxy
- Automatic SSL via Let's Encrypt
- Production-ready PostgreSQL
- Auto-restart on failure

See `DEPLOYMENT.md` for detailed instructions.

#### Option 2: Cloud Platforms

**Railway.app** (Easiest)
1. Connect GitHub repo
2. Add environment variables
3. Deploy automatically

**Render.com**
1. Create new Web Service
2. Connect repo
3. Set build command: `docker build`
4. Auto SSL included

**Fly.io**
```bash
fly launch
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

#### Option 3: AWS/GCP/Azure

- **Container**: ECS, Cloud Run, or Container Apps
- **Database**: RDS, Cloud SQL, or Azure Database
- **Load Balancer**: ALB/NLB with SSL certificate

### Production Checklist

- ✅ Configure proper DATABASE_URL (managed PostgreSQL recommended)
- ✅ Add OPENAI_API_KEY to environment
- ✅ Set DEBUG=false
- ✅ Configure CORS for your domains
- ✅ Implement authentication (JWT/OAuth/Portid)
- ✅ Setup SSL/HTTPS (Let's Encrypt or cloud provider)
- ✅ Configure backup strategy for database
- ✅ Setup monitoring and logging
- ✅ Implement rate limiting
- ✅ Add health checks to load balancer

### Environment Variables for Production

```bash
# Database (use managed PostgreSQL for production)
DATABASE_URL=postgresql://user:pass@your-db-host:5432/keepshot

# OpenAI
OPENAI_API_KEY=sk-your-production-key
OPENAI_MODEL=gpt-4o-mini

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Domain
ALLOWED_ORIGINS=https://keepshot.xyz,https://app.keepshot.xyz

# Monitoring
DEFAULT_CHECK_INTERVAL=60
MAX_CONCURRENT_CHECKS=20  # Increase for production

# Storage (use cloud storage for scale)
STORAGE_PATH=/app/storage
MAX_FILE_SIZE=100
```

---

## 🔌 Client Integration

### Mobile App (iOS/Android)

```swift
// iOS - Share Sheet Extension
import KeepShotSDK

// Configure SDK with your API endpoint
KeepShot.configure(
    apiURL: "https://api.keepshot.xyz",
    authProvider: PortIDAuthProvider()  // or your auth
)

func shareToKeepShot(url: URL) {
    KeepShot.shared.createBookmark(
        url: url,
        contentType: .url,
        monitoring: true
    )
}
```

### Browser Extension

```javascript
// Chrome Extension - Background Script
const API_URL = 'https://api.keepshot.xyz';  // or 'http://localhost:8000' for dev

chrome.bookmarks.onCreated.addListener((id, bookmark) => {
  fetch(`${API_URL}/api/v1/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': userId,
      'Authorization': `Bearer ${token}`  // Add your auth token
    },
    body: JSON.stringify({
      content_type: 'url',
      url: bookmark.url,
      title: bookmark.title,
      monitoring_enabled: true
    })
  });
});
```

### Web App

```typescript
// React Hook
import { useState, useEffect } from 'react';

const WS_URL = process.env.NODE_ENV === 'production'
  ? 'wss://api.keepshot.xyz'
  : 'ws://localhost:8000';

function useKeepShot(userId: string) {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/${userId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        setNotifications(prev => [data.data, ...prev]);
      }
    };

    return () => ws.close();
  }, [userId]);

  return { notifications };
}
```

---

## 🎨 Use Cases

### E-Commerce Price Tracking
Monitor product prices and get notified on drops:
```json
{
  "content_type": "url",
  "url": "https://amazon.com/product/...",
  "monitoring_enabled": true,
  "check_interval": 60
}
```

### Job Postings
Track job listings for status changes:
```json
{
  "content_type": "url",
  "url": "https://careers.company.com/job/...",
  "check_interval": 720
}
```

### News Articles
Monitor breaking news for updates:
```json
{
  "content_type": "url",
  "url": "https://news.com/article/...",
  "check_interval": 30
}
```

### Research Papers
Track academic papers for new versions:
```json
{
  "content_type": "pdf",
  "url": "https://arxiv.org/pdf/...",
  "check_interval": 1440
}
```

---

## 📊 Monitoring & Observability

### Health Check

```bash
# Local
curl http://localhost:8000/health

# Production
curl https://api.keepshot.xyz/health
```

### Metrics

```bash
# Local
curl http://localhost:8000/metrics

# Production
curl https://api.keepshot.xyz/metrics
```

### Logs

Structured JSON logs are written to stdout:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "info",
  "event": "bookmark_created",
  "bookmark_id": "123",
  "user_id": "user456"
}
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional content scrapers (Twitter, Reddit, etc.)
- More AI providers (Claude, Gemini)
- Advanced scheduling strategies
- Webhook support
- Analytics dashboard
- Mobile SDKs
- Browser extension templates

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [OpenAI](https://openai.com/)
- Scraped with [Playwright](https://playwright.dev/)

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**KeepShot** - Never miss an important update. Save once, get reminded forever. ✨
