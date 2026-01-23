# Cursor MCP Setup Guide

This guide explains how to configure Cursor to use the Tessie MCP server.

## Prerequisites

- Tessie MCP server running in SSE mode on port 8000
- Cursor editor installed

## Configuration

### Option 1: Local STDIO Mode (Recommended)

This is the simplest setup - Cursor runs the server as a subprocess.

**1. Open Cursor Settings**
- Go to Settings → Features → Model Context Protocol

**2. Add MCP Server Configuration**

Click "Edit Config" and add:

```json
{
  "mcpServers": {
    "tessie": {
      "command": "python",
      "args": [
        "-m",
        "src.server"
      ],
      "cwd": "/Users/ezelbayraktar/Development/tessie_mcp",
      "env": {
        "PYTHONPATH": "/Users/ezelbayraktar/Development/tessie_mcp"
      }
    }
  }
}
```

**3. Restart Cursor**

The Tessie MCP server will start automatically when Cursor launches.

### Option 2: SSE Mode (Remote Server)

Use this if you want to run the server separately or on a remote machine.

**1. Start the server manually:**
```bash
cd /Users/ezelbayraktar/Development/tessie_mcp
python -m src.server --transport sse --port 8000
```

**2. Configure Cursor**

In Cursor Settings → MCP, add:

```json
{
  "mcpServers": {
    "tessie": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

**3. Restart Cursor**

## Verification

### 1. Check Server is Running

Run the test script:
```bash
python test_mcp_client.py
```

You should see:
```
✅ Health check passed
✅ SSE endpoint accepts connections
✅ Messages endpoint accepts POST
```

### 2. Check Cursor Connection

In Cursor:
1. Open the Command Palette (Cmd+Shift+P / Ctrl+Shift+P)
2. Type "MCP: Show Status"
3. Look for "tessie" server
4. Status should be "Connected" or "Running"

### 3. Test Tool Access

In a Cursor chat:
1. Start a new conversation
2. Type: "What tools do you have available?"
3. You should see Tessie tools listed (get_battery_information, honk_horn, etc.)

## Troubleshooting

### Problem: "Server not connecting"

**Check 1: Server is running**
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","server":"tessie-mcp"}
```

**Check 2: Port not in use**
```bash
lsof -i :8000
# If something else is using port 8000, kill it or use a different port
```

**Check 3: Environment variables**
```bash
# Make sure .env file exists and has required vars
cat .env
# Should show TESSIE_TOKEN and VEHICLE_VIN
```

### Problem: "Tools not showing in Cursor"

**Check 1: MCP Protocol Version**
- Cursor might require specific MCP protocol version
- Check Cursor docs for compatibility

**Check 2: Restart Cursor**
- After changing MCP config, fully quit and restart Cursor
- Not just reload window - full quit

**Check 3: Check Cursor Logs**
- Open Cursor Developer Tools (Help → Toggle Developer Tools)
- Look in Console for MCP-related errors

### Problem: "Server crashes on connection"

**Check logs:**
```bash
# Run server with debug logging
python -m src.server --transport sse --port 8000 2>&1 | tee server.log
```

Look for errors in the logs and check:
- VIN is correct in .env
- TESSIE_TOKEN is valid
- Network connectivity to Tessie API

### Problem: "307 Redirect" or "Trailing slash issues"

This should be fixed in the latest version. If you still see it:
- Update to latest code
- Clear Cursor cache
- Restart Cursor completely

## Recommended: STDIO Mode

For most users, **STDIO mode is recommended** because:
- ✅ Simpler configuration
- ✅ Cursor manages server lifecycle
- ✅ Automatic restart on crashes
- ✅ No port conflicts
- ✅ Better isolation

Only use SSE mode if you need to:
- Share server across multiple clients
- Run server on a different machine
- Debug server independently

## Example Cursor Config (Complete)

Here's a complete example of a working Cursor MCP configuration:

```json
{
  "mcpServers": {
    "tessie": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/ezelbayraktar/Development/tessie_mcp",
      "env": {
        "PYTHONPATH": "/Users/ezelbayraktar/Development/tessie_mcp",
        "TESSIE_TOKEN": "your_token_here",
        "VEHICLE_VIN": "your_vin_here",
        "TELEMETRY_INTERVAL": "5"
      }
    }
  }
}
```

**Note:** You can put credentials directly in the config (as shown above) OR use the .env file. If using .env, the config becomes:

```json
{
  "mcpServers": {
    "tessie": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/ezelbayraktar/Development/tessie_mcp"
    }
  }
}
```

## Getting Help

If you're still having issues:

1. Run the test script: `python test_mcp_client.py`
2. Check server logs for errors
3. Check Cursor developer console for MCP errors
4. File an issue on GitHub with:
   - Cursor version
   - MCP config (with tokens redacted)
   - Server logs
   - Error messages

## Next Steps

Once connected, you can:
- Ask "What's my battery level?"
- Request "Flash the lights"
- Query "What's my tire pressure?"
- Control "Honk the horn"

See [AGENTS.md](AGENTS.md) for full list of available tools.
