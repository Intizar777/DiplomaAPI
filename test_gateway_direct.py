import asyncio
import httpx
from app.config import settings

async def test_gateway():
    """Test Gateway connection directly."""
    print(f"Gateway URL: {settings.gateway_url}")
    print(f"Timeout Connect: {settings.gateway_timeout_connect}")
    print(f"Timeout Read: {settings.gateway_timeout_read}")
    print(f"Email: {settings.gateway_auth_email}")
    
    timeout = httpx.Timeout(
        connect=settings.gateway_timeout_connect,
        read=settings.gateway_timeout_read,
        write=10.0,
        pool=10.0
    )
    
    async with httpx.AsyncClient(
        base_url=settings.gateway_url.rstrip("/"),
        timeout=timeout,
        follow_redirects=True
    ) as client:
        print("\nTesting login...")
        try:
            response = await client.post(
                "/auth/login",
                json={
                    "email": settings.gateway_auth_email,
                    "password": settings.gateway_auth_password
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_gateway())
