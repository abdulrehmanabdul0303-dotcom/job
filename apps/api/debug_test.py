import asyncio
import httpx
from app.main import app

async def debug_preferences():
    """Debug the preferences endpoint."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test without auth first
        response = await client.get("/api/v1/preferences/me")
        print(f"No auth - Status: {response.status_code}")
        print(f"No auth - Response: {response.text}")
        
        # Test with fake auth header
        headers = {"Authorization": "Bearer fake-token"}
        response = await client.get("/api/v1/preferences/me", headers=headers)
        print(f"Fake auth - Status: {response.status_code}")
        print(f"Fake auth - Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_preferences())