# KeepShot - Architecture

## Overview

KeepShot is a lightweight, AI-powered bookmark monitoring system designed to be:
- **Auth-agnostic**: Bring your own authentication (JWT, OAuth, API keys, Portid, etc.)
- **Multi-content**: Supports URLs, images, videos, PDFs, and text
- **Intelligent**: AI decides what's worth monitoring
- **Lightweight**: No Redis/Celery overhead
- **Plug-and-play**: Docker Compose up and running

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  (Mobile App, Web Extension, Web App - any auth system)     │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  API Layer   │  │  AI Engine   │  │  Scheduler   │     │
│  │  (REST/WS)   │  │  (OpenAI)    │  │(APScheduler) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Content    │  │    Change    │  │Notification  │     │
│  │   Scraper    │  │   Detector   │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│  PostgreSQL  │          │ File Storage │
│   Database   │          │   (Local)    │
└──────────────┘          └──────────────┘
```

## Core Components

### 1. API Layer
- **Auth-agnostic middleware**: Validates `user_id` from headers/tokens
- **REST endpoints**: CRUD operations for bookmarks
- **WebSocket**: Real-time notifications
- **OpenAPI docs**: Auto-generated API documentation

### 2. Content Scraper
Handles multiple content types:
- **URLs**: Playwright (JS-heavy) + httpx (static pages)
- **Images**: Direct download + metadata extraction
- **Videos**: Metadata extraction (yt-dlp)
- **PDFs**: Text extraction (PyPDF2)
- **Text**: Direct storage

### 3. AI Engine (OpenAI)
- **Watchpoint extraction**: Identifies key fields to monitor
- **Significance detection**: Determines what changes matter
- **Notification generation**: Creates human-friendly messages
- **Duplicate detection**: Identifies similar/duplicate content
- **Related content**: Finds connections between bookmarks

### 4. Change Detector
- **Content hashing**: Detects any changes
- **Smart comparison**: Compares watchpoints, not entire content
- **Configurable sensitivity**: Per-bookmark monitoring settings

### 5. Background Scheduler (APScheduler)
- **Periodic checks**: Configurable intervals per bookmark
- **Smart scheduling**: More frequent checks for volatile content
- **Resource-aware**: Lightweight, no external dependencies

### 6. Notification Service
- **WebSocket push**: Real-time updates to connected clients
- **Database storage**: Persistent notification history
- **Webhook support**: POST to external URLs (optional)

## Database Schema

### Users
```sql
- id (UUID, PK)
- created_at (timestamp)
- metadata (JSONB) -- for builder's custom data
```

### Bookmarks
```sql
- id (UUID, PK)
- user_id (UUID, FK)
- content_type (ENUM: url, image, video, pdf, text)
- url (TEXT) -- nullable for text snippets
- title (TEXT)
- description (TEXT)
- raw_content (TEXT) -- for text snippets
- file_path (TEXT) -- for downloaded files
- metadata (JSONB) -- platform-specific (tweet_id, author, etc.)
- monitoring_enabled (BOOLEAN)
- check_interval (INTEGER) -- minutes
- created_at (timestamp)
- last_checked_at (timestamp)
```

### Snapshots
```sql
- id (UUID, PK)
- bookmark_id (UUID, FK)
- content_hash (TEXT) -- SHA256 of content
- extracted_content (TEXT) -- cleaned/processed content
- snapshot_data (JSONB) -- full snapshot
- created_at (timestamp)
```

### Watchpoints
```sql
- id (UUID, PK)
- snapshot_id (UUID, FK)
- field_name (TEXT) -- e.g., "price", "title", "availability"
- field_value (TEXT)
- field_type (TEXT) -- e.g., "currency", "string", "number"
- is_primary (BOOLEAN) -- main thing to monitor
- created_at (timestamp)
```

### Changes
```sql
- id (UUID, PK)
- watchpoint_id (UUID, FK)
- old_value (TEXT)
- new_value (TEXT)
- change_type (TEXT) -- increase, decrease, modified, added, removed
- significance_score (FLOAT) -- AI-determined importance (0-1)
- detected_at (timestamp)
```

### Notifications
```sql
- id (UUID, PK)
- user_id (UUID, FK)
- bookmark_id (UUID, FK)
- change_id (UUID, FK, nullable)
- notification_type (ENUM: change, duplicate, related, reminder)
- title (TEXT)
- message (TEXT)
- read (BOOLEAN)
- created_at (timestamp)
```

## API Endpoints

### Bookmarks
- `POST /api/v1/bookmarks` - Create bookmark
- `GET /api/v1/bookmarks` - List user's bookmarks (paginated)
- `GET /api/v1/bookmarks/{id}` - Get bookmark details
- `PATCH /api/v1/bookmarks/{id}` - Update bookmark settings
- `DELETE /api/v1/bookmarks/{id}` - Delete bookmark

### Notifications
- `GET /api/v1/notifications` - List notifications (paginated)
- `GET /api/v1/notifications/{id}` - Get notification details
- `PATCH /api/v1/notifications/{id}` - Mark as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### Monitoring
- `POST /api/v1/bookmarks/{id}/check` - Trigger immediate check
- `GET /api/v1/bookmarks/{id}/history` - Get change history

### WebSocket
- `WS /ws/{user_id}` - Real-time notification stream

### Health
- `GET /health` - Health check
- `GET /metrics` - System metrics

## Content Processing Flow

### 1. Bookmark Creation
```
User submits bookmark
    ↓
Validate content type
    ↓
Fetch/download content
    ↓
Extract text/metadata
    ↓
Create initial snapshot
    ↓
Send to AI for watchpoint extraction
    ↓
Store watchpoints
    ↓
Schedule monitoring (if enabled)
    ↓
Return bookmark ID
```

### 2. Monitoring Cycle
```
Scheduler triggers check
    ↓
Fetch current content
    ↓
Create new snapshot
    ↓
Compare with last snapshot
    ↓
If changed:
  ↓
  Identify specific changes
  ↓
  AI determines significance
  ↓
  If significant:
    ↓
    Generate notification message
    ↓
    Store notification
    ↓
    Push via WebSocket
```

### 3. AI Watchpoint Extraction

**Input**: Raw content + content type
**Process**:
1. Extract structured data based on type
2. Identify key fields (AI-powered)
3. Determine monitoring priority
4. Set check intervals

**Output**: List of watchpoints with priorities

**Examples**:
- **E-commerce URL**: Price, availability, rating, reviews
- **Article**: Title, publication date, content sections
- **Social post**: Text, likes, replies, shares
- **Job posting**: Status, salary, location
- **PDF**: Page count, key sections, metadata

## AI Prompts

### Watchpoint Extraction
```
Content Type: {type}
Content: {content}

Extract 3-5 key fields that are most likely to change and matter to the user.
For each field provide:
1. field_name (short identifier)
2. field_value (current value)
3. field_type (data type)
4. is_primary (true if most important)
5. reasoning (why this matters)

Format as JSON array.
```

### Change Significance
```
Field: {field_name}
Old Value: {old_value}
New Value: {new_value}
Content Type: {content_type}

Rate the significance of this change from 0.0 to 1.0 where:
0.0 = trivial (e.g., typo fix)
1.0 = critical (e.g., price drop 50%, item sold out)

Also provide a brief explanation.
```

### Notification Generation
```
Bookmark: {title}
Change Type: {change_type}
Changes: {changes_list}
Significance: {significance_score}

Generate a concise, friendly notification message (max 100 chars) that:
1. Clearly states what changed
2. Explains why it matters
3. Uses appropriate tone (urgent for high significance)

Format: Plain text message
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/keepshot

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # Cheaper for most tasks

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

# Auth (optional - for reference implementations)
JWT_SECRET=your-secret-key  # Only if using JWT middleware
```

### Docker Compose
- FastAPI app container
- PostgreSQL database
- Volume mounts for storage
- Health checks
- Auto-restart

## Deployment

### Quick Start
```bash
git clone <repo>
cd keepshot
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

### Manual Installation
```bash
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Authentication Integration

The system is **auth-agnostic**. Implement custom middleware:

### Example: JWT Middleware
```python
from fastapi import Request, HTTPException
import jwt

async def auth_middleware(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(401, "Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY)
        request.state.user_id = payload["user_id"]
    except:
        raise HTTPException(401, "Invalid token")
```

### Example: Portid Integration
```python
from harboria_portid import PortIDClient

async def portid_middleware(request: Request):
    token = request.headers.get("X-Portid-Token")
    # Validate with Portid sync server
    user_id = validate_portid_token(token)
    request.state.user_id = user_id
```

### Example: API Key
```python
async def apikey_middleware(request: Request):
    api_key = request.headers.get("X-API-Key")
    # Look up user by API key
    user = db.query(User).filter_by(api_key=api_key).first()
    if not user:
        raise HTTPException(401, "Invalid API key")
    request.state.user_id = user.id
```

## Performance Considerations

- **Caching**: Response caching for list endpoints
- **Connection pooling**: PostgreSQL connection pool
- **Rate limiting**: Per-user API rate limits
- **Batch processing**: Monitor multiple bookmarks concurrently
- **Lazy loading**: Only fetch full content when needed
- **Indexing**: Database indexes on frequently queried fields

## Security

- **Input validation**: Pydantic models for all inputs
- **SQL injection**: SQLAlchemy ORM (no raw queries)
- **XSS prevention**: Content sanitization
- **File upload limits**: Max file size enforcement
- **Rate limiting**: Prevent abuse
- **CORS**: Configurable allowed origins
- **HTTPS**: TLS in production (via reverse proxy)

## Monitoring & Observability

- **Structured logging**: JSON logs with context
- **Health checks**: `/health` endpoint
- **Metrics**: Prometheus-compatible `/metrics`
- **Error tracking**: Automatic error logging
- **Performance**: Request timing in logs

## Extensibility

### Custom Content Scrapers
```python
from app.scrapers.base import ContentScraper

class CustomScraper(ContentScraper):
    async def scrape(self, url: str) -> dict:
        # Custom logic
        return {"content": "..."}
```

### Custom AI Providers
```python
from app.ai.base import AIProvider

class CustomAI(AIProvider):
    async def extract_watchpoints(self, content: str) -> list:
        # Custom AI logic
        return [...]
```

### Webhook Notifications
```python
# POST to external URL when notification created
WEBHOOK_URL=https://your-service.com/webhook
```

## Production Deployment

### Official Instance: keepshot.xyz

**Production API:** `https://api.keepshot.xyz`

#### Architecture in Production

```
                    ┌──────────────────┐
                    │   keepshot.xyz   │
                    │   (Frontend)     │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
    Internet ───────┤  Nginx + SSL     │
                    │  (Let's Encrypt) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  FastAPI Backend │
                    │  (Docker)        │
                    └────────┬─────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │                                   │
    ┌──────▼──────┐                   ┌───────▼──────┐
    │ PostgreSQL  │                   │File Storage  │
    │  (Docker)   │                   │   (Volume)   │
    └─────────────┘                   └──────────────┘
```

#### Production Stack Components

1. **Nginx**
   - Reverse proxy
   - SSL/TLS termination
   - Rate limiting (100 req/min)
   - WebSocket support
   - CORS configuration

2. **Let's Encrypt**
   - Automatic SSL certificates
   - Auto-renewal every 12 hours
   - TLS 1.2+ only

3. **FastAPI Application**
   - Multiple worker processes
   - Health checks
   - Auto-restart on failure
   - Structured JSON logging

4. **PostgreSQL**
   - Persistent volumes
   - Regular backups
   - Connection pooling
   - Performance indexes

#### Deployment Methods

**Option 1: VPS Deployment** (Recommended for keepshot.xyz)
```bash
# One-command setup
curl -sSL https://raw.githubusercontent.com/yourusername/keepshot/main/setup-production.sh | sudo bash
```

**Option 2: Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Option 3: Cloud Platforms**
- Railway.app (easiest)
- Render.com (includes SSL)
- Fly.io (global edge deployment)

See `DEPLOYMENT.md` for detailed instructions.

#### Production Configuration

```bash
# Production environment
DATABASE_URL=postgresql://user:pass@db:5432/keepshot_prod
OPENAI_API_KEY=sk-production-key
OPENAI_MODEL=gpt-4o-mini
DEBUG=false
ALLOWED_ORIGINS=https://keepshot.xyz,https://app.keepshot.xyz
```

#### Monitoring Endpoints

```bash
# Health check
curl https://api.keepshot.xyz/health

# Metrics
curl https://api.keepshot.xyz/metrics

# API Documentation
open https://api.keepshot.xyz/docs
```

#### Security in Production

- ✅ HTTPS enforced (Let's Encrypt SSL)
- ✅ Rate limiting (Nginx)
- ✅ CORS configured for specific domains
- ✅ Database password secured
- ✅ API keys in environment variables
- ✅ Firewall configured (ports 80, 443)
- ✅ Regular security updates

## Future Enhancements

- [ ] Browser extension reference implementation
- [ ] Mobile app SDKs (Swift, Kotlin)
- [ ] Advanced scheduling (time-of-day optimization)
- [ ] ML-based change prediction
- [ ] Multi-language support
- [ ] Collaborative bookmarks (shared monitoring)
- [ ] Export/import functionality
- [ ] Analytics dashboard
- [ ] Plugin system for custom scrapers
- [ ] CDN integration for global performance
- [ ] Redis caching layer
- [ ] Managed database migration (AWS RDS, Cloud SQL)
