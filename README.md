KeepShot 

Overview

KeepShot is a real-time AI-powered bookmark monitoring and reminder system. It allows users to save bookmarks, tracks content changes, and delivers context-aware reminders using AI. The system intelligently identifies significant changes, related content, or duplicates and notifies users via push notifications, keeping them updated without manual checking.

⸻

Key Features
	1.	AI-Powered Watchpoints
	•	Extracts meaningful watchpoints from saved bookmarks using OpenAI.
	•	Identifies key information to monitor for changes automatically.
	2.	Snapshot-Based Change Detection
	•	Periodically takes snapshots of bookmarked content.
	•	Compares snapshots to detect significant content changes.
	3.	Dynamic Reminder Generation
	•	AI generates reminders for:
	•	Content changes
	•	Related saves
	•	Duplicate saves
	•	Messages are concise, actionable, and user-friendly.
	4.	Real-Time Push Notifications
	•	WebSocket-based notifications ensure users are updated instantly.
	5.	Database Persistence
	•	Stores bookmarks, snapshots, watchpoints, and reminders.
	•	Fully trackable history for user analytics and auditing.
	6.	Async Monitoring System
	•	Uses Celery + Redis to perform background monitoring of saved bookmarks without blocking the main app.
	7.	Frontend Dashboard
	•	Minimal Tailwind-based UI for notifications display.
	•	Real-time updates via WebSocket.

	
	[User] 
   │
   ▼
[Save Bookmark via API]
   │
   ▼
[Scraper] --> [Snapshot saved in DB]
   │
   ▼
[AI Watchpoint Extraction] --> [Watchpoints saved in DB]
   │
   ▼
[Celery Monitoring Task]
   │
   ├─> Fetch latest content
   ├─> Compare with last snapshot
   ├─> Detect significant change
   ├─> Generate AI reminder (change, related, duplicate)
   └─> Save reminder + push notification via WebSocket
	 
	 
	 
	 
	 
	 keepshot/
├── app/
│   ├── main.py               # FastAPI app + WebSocket dashboard
│   ├── config.py             # Environment and config settings
│   ├── database.py           # SQLAlchemy session and Base
│   ├── models/               # DB models: bookmarks, snapshots, watchpoints, reminders
│   ├── routers/              # API routers: bookmarks, reminders
│   ├── services/             # Core services: scraper, AI parser, prompts, notifications
│   └── tasks/                # Celery async tasks (monitoring)
├── celery.py                 # Celery configuration
├── requirements.txt          # Python dependencies
├── .env                      # Secrets and environment variables
└── README.md


Core Flow
	1.	User saves a bookmark
	•	POST /api/bookmark
	•	Scraper fetches content and stores it in Snapshot.
	2.	AI extracts watchpoints
	•	Identifies important fields from the content.
	•	Saved to WatchPoint table.
	3.	Async monitoring task
	•	Celery periodically fetches bookmark content.
	•	Compares with previous snapshots.
	•	Detects significant changes or related/duplicate saves.
	4.	AI generates reminders
	•	Uses contextual prompt templates for change, related, or duplicate notifications.
	•	Reminder saved in Reminder table.
	5.	Push notification
	•	WebSocket pushes message to the dashboard in real-time.

	
	
	DATABASE_URL=postgresql://username:password@localhost:5432/keepshot
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-XXXXXXXXXXXX
	
	
	
	Future Improvements
	•	Add user authentication and multi-user support.
	•	Refine AI significance detection to reduce false alerts.
	•	Enhance frontend UI for bookmark management, reminders, and analytics.
	•	Add rate-limiting and retry logic for scraper and AI calls.

⸻

KeepShot v1.0 enables users to “save once, get reminded forever” with AI-driven insights.
	