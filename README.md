# Tessie MCP Server

A Model Context Protocol (MCP) server that wraps the Tessie API so LLM clients (Cursor, Claude, etc.) can query and control a configured Tesla using efficient, focused API endpoints.

## Status
- **Telemetry:** Fully implemented with both legacy (full state) and new specialized endpoints for efficient data retrieval.
- **Control:** `honk_horn` and `flash_lights` are live and functional. Lock/unlock and climate control are scaffolded.
- **Breaking change:** Now uses VIN instead of license plate for vehicle identification.
- Breaking changes are possible until the first stable tag is cut.

## Quick Start
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` and set your Tessie API token and vehicle VIN:
```env
TESSIE_TOKEN=your_tessie_api_token_here
VEHICLE_VIN=5YJ3E1EA1KF123456  # Your Tesla VIN
TELEMETRY_INTERVAL=5           # minutes; use 'realtime' to skip caching
```

Run the server (STDIO by default):
```bash
python -m src.server
```

Remote/SSE mode (for network clients):
```bash
python -m src.server --transport sse --host 0.0.0.0 --port 8000
```

## What To Expect
- **New Specialized Telemetry Endpoints:** Efficient, focused API calls for battery, battery health, location, tire pressure, and vehicle status.
- **Legacy Telemetry Tools:** Full vehicle state fetch with all traditional metrics still available.
- **Working Control Actions:** `honk_horn` and `flash_lights` execute real commands on your Tesla.
- Tessie-backed auth and caching; respects refresh intervals from `.env`.
- VIN-based vehicle identification for improved reliability.

## Repo Layout
- `src/server.py` — MCP entrypoint; loads telemetry + control tools, handles VIN configuration.
- `src/telemetry/service.py` — Telemetry retrieval with caching and specialized endpoint methods.
- `src/telemetry/tools.py` — Telemetry tool registry/dispatch (new + legacy tools).
- `src/control/service.py` — Control actions with real implementations for honk/flash.
- `src/control/tools.py` — Control tool registry/dispatch.
- `src/tessie_client.py` — Tessie REST client with VIN-based endpoints for telemetry and control.

## Available Tools

### New Specialized Telemetry (Recommended)
- `get_battery_information` — Battery level, drain, energy, voltage, current, temperature
- `get_battery_health_information` — Battery capacity and max range
- `get_location_information` — GPS coordinates with address
- `get_tire_pressure_information` — All tire pressures with status
- `get_vehicle_status` — Sleep/wake status

### Control (Live)
- `honk_horn` — Honk the vehicle horn (⚠️ real action)
- `flash_lights` — Flash the vehicle lights (⚠️ real action)

### Roadmap
- Complete lock/unlock door control
- Implement climate control (start/stop)
- Add charging control
- Trunk/frunk control

See [AGENTS.md](AGENTS.md) for complete tool documentation.
