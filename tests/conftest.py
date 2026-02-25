"""
Test configuration and shared fixtures.

Environment variables and module stubs are set BEFORE any app imports so that:
- pydantic-settings picks them up when Settings() is first instantiated.
- Heavy optional dependencies that are not installed in the test environment
  are replaced with MagicMock stubs so the app can be imported without error.
"""
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# ── 1. Env vars (must come before any app import) ─────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_keepshot.db")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-unit-tests-only")
os.environ.setdefault("STORAGE_PATH", "/tmp/keepshot_test")
os.environ.setdefault("DEBUG", "false")

# ── 2. Stub heavy optional packages (scraper / AI) ────────────────────────────
# These are only needed at runtime when actually scraping/AI-calling. Tests
# mock the service layer, so we just need clean imports.
_STUBS = [
    "aiohttp", "aiohttp.ClientSession",
    "playwright", "playwright.async_api",
    "bs4", "beautifulsoup4",
    "PyPDF2",
    "PIL", "PIL.Image",
    "yt_dlp",
    "openai", "openai.AsyncOpenAI",
    "python_magic", "magic",
    "lxml",
]
for _mod in _STUBS:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# ── 3. Normal imports (app can now be safely imported) ────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.dependencies import create_access_token
from app.models.user import User

SQLITE_URL = "sqlite:///./test_keepshot.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_keepshot.db"):
        os.remove("./test_keepshot.db")


@pytest.fixture
def db():
    """
    DB session rolled back after each test for isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    """TestClient with DB overridden and scheduler/storage mocked."""
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.start_scheduler"), patch("app.main.stop_scheduler"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """A pre-created user row in the test database."""
    user = User(id="test-user-uuid", username="testuser", password_hash="placeholder")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """A valid JWT for the test user."""
    return create_access_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Authorization header dict for the test user."""
    return {"Authorization": f"Bearer {auth_token}"}
