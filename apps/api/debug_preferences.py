import asyncio
import httpx
from app.main import app

async def debug_preferences_response():
    """Debug the actual preferences response."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        
        # First register a user to get auth token
        register_response = await client.post("/api/v1/auth/register", json={
            "email": "debug@example.com",
            "password": "TestPassword123!",
            "full_name": "Debug User"
        })
        
        if register_response.status_code in [200, 201]:
            token = register_response.json()["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
            
            # Test the preferences endpoint
            response = await client.get("/api/v1/preferences/me", headers=auth_headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            try:
                print(f"JSON: {response.json()}")
            except:
                print("Could not parse JSON")
        else:
            print(f"Registration failed: {register_response.status_code} - {register_response.text}")

if __name__ == "__main__":
    asyncio.run(debug_preferences_response())