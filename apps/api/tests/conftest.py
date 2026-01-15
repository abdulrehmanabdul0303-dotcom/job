"""
Pytest configuration and fixtures for testing.
Enhanced with comprehensive test data factories and deterministic setup.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.services.auth import create_access_token, get_password_hash
from io import BytesIO
from tests.factories import test_data_builder

# CRITICAL: Import all models so they register with Base.metadata
import app.models  # This imports all models

# Test database URL (use separate test database)
# Handle SQLite vs PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./jobpilot_test.db"
else:
    TEST_DATABASE_URL = settings.DATABASE_URL.replace("/jobpilot", "/jobpilot_test")

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    ✅ CREATE TABLES BEFORE TESTS
    ✅ DROP SAFELY EVEN IF TABLES MISSING
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables after test (checkfirst=True prevents errors if tables missing)
    async with test_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(sync_conn, checkfirst=True))


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database session override.
    Uses ASGITransport for httpx compatibility.
    """
    async def override_get_db():
        yield db_session
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport for new httpx versions
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication tests."""
    user = test_data_builder.user_factory.create_user(
        email="testuser@example.com",
        password="TestPass123!"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_password() -> str:
    """Return the test user password."""
    return "TestPass123!"


@pytest.fixture
async def auth_cookies(client: AsyncClient, test_user: User, test_password: str) -> dict:
    """Get authentication cookies for cookie-based auth."""
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "email": test_user.email,
            "password": test_password
        }
    )
    return response.cookies


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user: User, test_password: str) -> dict:
    """Get authorization headers with valid token - DEPRECATED for cookie auth."""
    # This fixture is deprecated since we use cookie-based auth
    # For cookie auth tests, use the cookies directly from login response
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={
            "email": test_user.email,
            "password": test_password
        }
    )
    # Return empty headers since we use cookies now
    return {}


@pytest.fixture
async def complete_user_scenario(db_session: AsyncSession):
    """Create a complete user scenario with all related data."""
    return await test_data_builder.create_complete_user_scenario(db_session)


@pytest.fixture
async def multiple_users_scenario(db_session: AsyncSession):
    """Create multiple users with complete data for testing."""
    return await test_data_builder.create_multiple_users_scenario(db_session, count=3)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create a minimal valid PDF for testing."""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Resume) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
0000000308 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
387
%%EOF"""
    return pdf_content


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Create a minimal valid DOCX for testing."""
    # Minimal DOCX is a ZIP file with specific structure
    import zipfile
    from io import BytesIO
    
    docx_buffer = BytesIO()
    with zipfile.ZipFile(docx_buffer, 'w') as docx:
        # Add [Content_Types].xml
        docx.writestr('[Content_Types].xml', 
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>')
        
        # Add _rels/.rels
        docx.writestr('_rels/.rels',
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
        
        # Add word/document.xml
        docx.writestr('word/document.xml',
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>Sample Resume</w:t></w:r></w:p></w:body>'
            '</w:document>')
    
    docx_buffer.seek(0)
    return docx_buffer.getvalue()


@pytest.fixture
def sample_resume_data():
    """Get sample resume data for testing."""
    return test_data_builder.resume_factory.get_sample_resume_data()


@pytest.fixture
def performance_test_data():
    """Get large dataset for performance testing."""
    return test_data_builder.create_performance_test_data()


# Test markers
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
