#!/usr/bin/env python3
"""Test STDIO MCP server."""

import asyncio
import json
import sys
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.server import app, get_config, init_services

async def test_stdio():
    """Test MCP server in STDIO mode."""
    print("Testing STDIO MCP Server", file=sys.stderr)
    print("="*60, file=sys.stderr)

    # Initialize services
    vin, interval = get_config()
    init_services(vin, interval)
    print(f"✅ Services initialized", file=sys.stderr)

    # Test list_tools
    print("\nTesting list_tools()...", file=sys.stderr)
    tools = await app._tool_handlers["tools/list"]()

    print(f"Tools returned: {len(tools) if tools else 0}", file=sys.stderr)

    if tools:
        print(f"✅ Got {len(tools)} tools", file=sys.stderr)
        print("\nFirst 5 tools:", file=sys.stderr)
        for tool in tools[:5]:
            print(f"  - {tool.name}", file=sys.stderr)
    else:
        print("❌ ERROR: No tools returned!", file=sys.stderr)

    return tools

if __name__ == "__main__":
    tools = asyncio.run(test_stdio())
    sys.exit(0 if tools else 1)
