#!/usr/bin/env python3
"""Simple test client for the Tessie MCP server (SSE mode).

This script tests that the MCP server is responding correctly.
"""

import asyncio
import json
import httpx


async def test_mcp_server():
    """Test MCP server endpoints."""
    base_url = "http://localhost:8000"

    print("Testing Tessie MCP Server...")
    print("="*60)

    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            assert response.status_code == 200
            print("   ✅ Health check passed")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return

    # Test 2: SSE endpoint (should accept GET)
    print("\n2. Testing SSE endpoint availability...")
    async with httpx.AsyncClient() as client:
        try:
            # Try to connect to SSE
            async with client.stream("GET", f"{base_url}/sse") as response:
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    print("   ✅ SSE endpoint accepts connections")
                else:
                    print(f"   ❌ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  SSE test: {e}")

    # Test 3: Messages endpoint (should accept POST)
    print("\n3. Testing messages endpoint...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Try POST to messages
            response = await client.post(
                f"{base_url}/messages",
                json={"test": "message"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 202, 204]:
                print("   ✅ Messages endpoint accepts POST")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Messages test: {e}")

    print("\n" + "="*60)
    print("✅ Basic connectivity tests completed!")
    print("\nIf all tests passed, the server is running correctly.")
    print("Check your Cursor MCP configuration.")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
