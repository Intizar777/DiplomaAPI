import asyncio
import socket
import httpx
from app.config import settings

async def test_dns_resolution():
    """Test DNS resolution of Gateway URL."""
    gateway_url = settings.gateway_url
    hostname = gateway_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    print(f"Testing DNS resolution for: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"DNS resolved to: {ip}")
    except Exception as e:
        print(f"DNS resolution failed: {e}")

async def test_http_connectivity():
    """Test HTTP connectivity to Gateway."""
    gateway_url = settings.gateway_url
    print(f"\nTesting HTTP connectivity to: {gateway_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test just connectivity, not auth
            response = await client.get(f"{gateway_url}/health")
            print(f"Health check: {response.status_code}")
    except httpx.TimeoutException as e:
        print(f"HTTP timeout: {e}")
    except Exception as e:
        print(f"HTTP error: {type(e).__name__}: {e}")

async def test_login_connectivity():
    """Test login endpoint connectivity."""
    gateway_url = settings.gateway_url
    print(f"\nTesting login endpoint: {gateway_url}/auth/login")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{gateway_url}/auth/login",
                json={
                    "email": settings.gateway_auth_email,
                    "password": settings.gateway_auth_password
                }
            )
            print(f"Login response: {response.status_code}")
            print(f"Response length: {len(response.text)}")
    except httpx.TimeoutException as e:
        print(f"Login timeout: {e}")
    except Exception as e:
        print(f"Login error: {type(e).__name__}: {e}")

async def main():
    await test_dns_resolution()
    await test_http_connectivity()
    await test_login_connectivity()

if __name__ == "__main__":
    asyncio.run(main())
