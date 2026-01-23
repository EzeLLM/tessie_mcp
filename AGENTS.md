# Tessie MCP – Agent Guide

This repo hosts an MCP server that exposes Tesla telemetry and control via the Tessie API for LLM-based agents such as Cursor and Claude.

## Status (2025-11-29)
- Telemetry: implemented with both legacy (full state) and new efficient specialized endpoints.
- Control: honk/flash, lock/unlock, climate start/stop, and temperature set are implemented.
- Vehicles are now identified by VIN instead of license plate.
- Expect breaking changes until the first stable tag.

## How To Run
- Entry point: `python -m src.server` (STDIO) or `python -m src.server --transport sse --port 8000` (SSE).
- Config: `.env` in repo root. Required `TESSIE_TOKEN` and `VEHICLE_VIN`; optional `TELEMETRY_INTERVAL` (minutes or `realtime`, defaults to 5).
- Server id: `tessie-mcp`.

## Package Layout
- `src/server.py` — MCP server; merges telemetry + control tool registries and dispatch.
- `src/telemetry/service.py` — Telemetry retrieval/caching with specialized endpoint methods.
- `src/telemetry/tools.py` — Telemetry tool specs and dispatch map.
- `src/control/service.py` — Control service with real API calls for honk/flash, lock/unlock, climate control, and temperature setting.
- `src/control/tools.py` — Control tool specs and dispatch map.
- `src/tessie_client.py` — Tessie REST client supporting VIN-based endpoints (auth via `TESSIE_TOKEN`).

## Telemetry Behavior
- Caching: refreshes on first access; then every `TELEMETRY_INTERVAL` minutes unless set to `realtime`.
- Error handling: raises if vehicle VIN cannot be found.
- Output: human-readable strings tuned for LLM consumption; raw values available via private `_get_*` methods.
- Two categories: **New efficient specialized endpoints** (recommended) and **Legacy tools** (full state fetch).

### Telemetry Tools (MCP)

**New Specialized Endpoints (Recommended):**
- `get_battery_information` — Detailed battery data including level, phantom drain, energy, voltage, current, and temperature with data age tracking
- `get_battery_health_information` — Battery health metrics including max range, ideal range, and capacity
- `get_location_information` — GPS coordinates with address and saved location name
- `get_tire_pressure_information` — All four tire pressures (in bar) with status indicators
- `get_vehicle_status` — Sleep/wake status (asleep, waiting_for_sleep, or awake)

**Legacy Tools (Full State Fetch):**
Battery/charging: `get_battery_level`, `get_charging_state`, `get_minutes_to_full_charge`, `get_energy_remaining`, `get_lifetime_energy_used`; climate/heaters: `get_allow_cabin_overheat_protection`, `get_outside_temp`, `get_is_climate_on`, `get_supports_fan_only_cabin_overheat_protection`, seat heaters (`get_seat_heater_left/right/rear_*`), other heaters (`get_side_mirror_heaters`, `get_steering_wheel_heater`, `get_wiper_blade_heater`); drive/location: `get_location`, `get_power`, `get_speed`, `get_shift_state`, `get_active_route`; security/info: `get_sentry_mode`, `get_display_name`; summaries: `get_all_heater_status`, `get_battery_summary`; service: `get_in_service`.

### Control Tools

**Implemented:**
- `honk_horn` — Honk the vehicle horn (real API call)
- `flash_lights` — Flash the vehicle lights (real API call)
- `lock_doors` / `unlock_doors` — Lock/unlock the vehicle (real API calls)
- `start_climate` / `stop_climate` — Start/stop climate or preconditioning (real API calls)
- `set_temperature` — Set cabin temperature in Celsius (supports wait_for_completion flag)

## Usage Notes for Agents
- **Prefer new specialized telemetry endpoints** (`get_battery_information`, etc.) over legacy tools for better performance.
- Control tools: `honk_horn` and `flash_lights` are fully operational and will trigger real vehicle actions.
- Arguments: most tools take no parameters; `set_temperature` expects `temperature` (Celsius) and optional `wait_for_completion`.
- SSE mode: endpoints `/sse` and `/messages`; health at `/health`.
- Vehicle identification: Use VIN (e.g., `5YJ3E1EA1KF123456`) instead of license plate.

## Safety & Expectations
- **Warning:** `honk_horn` and `flash_lights` will trigger real vehicle actions. Use responsibly.
- Other control actions also call the live Tessie API; use only when intended.
- Be prepared for minor API/shape changes until the first stable tag.
