

# Tessie MCP - Development Guide

This document provides detailed information for developers working on the Tessie MCP server, including architecture, debugging techniques, and contribution guidelines.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Code Organization](#code-organization)
- [Development Setup](#development-setup)
- [Debugging](#debugging)
- [Testing](#testing)
- [Adding New Features](#adding-new-features)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [Best Practices](#best-practices)

## Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Server                            │
│                      (src/server.py)                         │
│  - Handles MCP protocol                                      │
│  - Routes tool calls to services                            │
│  - Manages server lifecycle (STDIO/SSE)                     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
       ┌───────▼────────┐           ┌────────▼────────┐
       │   Telemetry    │           │    Control       │
       │    Service     │           │    Service       │
       │ (telemetry/)   │           │  (control/)      │
       └───────┬────────┘           └────────┬─────────┘
               │                              │
               └──────────┬───────────────────┘
                          │
                  ┌───────▼────────┐
                  │ Tessie Client  │
                  │(tessie_client) │
                  │ - API calls    │
                  │ - Retry logic  │
                  │ - Auth         │
                  └────────────────┘
```

### Module Responsibilities

- **`server.py`**: MCP protocol handler, tool registration, server lifecycle
- **`telemetry/service.py`**: Vehicle data retrieval with caching
- **`telemetry/tools.py`**: Telemetry tool definitions and dispatch
- **`control/service.py`**: Vehicle command execution
- **`control/tools.py`**: Control tool definitions and dispatch
- **`tessie_client.py`**: Low-level Tessie API client with retry logic
- **`exceptions.py`**: Custom exception hierarchy
- **`constants.py`**: Configuration constants and magic numbers
- **`utils.py`**: Shared utility functions (logging, formatting, validation)

## Code Organization

### Directory Structure

```
tessie_mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP server entry point
│   ├── tessie_client.py       # Tessie API client
│   ├── exceptions.py          # Custom exceptions
│   ├── constants.py           # Constants and config
│   ├── utils.py               # Utility functions
│   ├── telemetry/
│   │   ├── __init__.py
│   │   ├── service.py         # Telemetry logic
│   │   └── tools.py           # Tool definitions
│   └── control/
│       ├── __init__.py
│       ├── service.py         # Control logic
│       └── tools.py           # Tool definitions
├── .env                       # Environment config (not in git)
├── .env.example               # Example config
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation
├── AGENTS.md                  # Agent integration guide
└── DEVELOPMENT.md             # This file
```

### Design Patterns

**1. Service Layer Pattern**
- Services (`Telemetry`, `Control`) encapsulate business logic
- Thin controllers (tool handlers) delegate to services
- Clear separation of concerns

**2. Dependency Injection**
- Services accept optional `TessieClient` instance
- Enables testing with mock clients
- Example:
  ```python
  telemetry = Telemetry(vin="...", client=mock_client)
  ```

**3. Exception Hierarchy**
- All custom exceptions inherit from `TessieMCPError`
- Enables catching all app errors: `except TessieMCPError`
- Specific exceptions for specific failures

## Development Setup

### Prerequisites
- Python 3.10+
- Tessie API token (get from tessie.com)
- Access to a Tesla vehicle via Tessie

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd tessie_mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your TESSIE_TOKEN and VEHICLE_VIN
```

### Running in Development Mode

```bash
# Run with STDIO transport (for local testing)
python -m src.server

# Run with SSE transport (for network clients)
python -m src.server --transport sse --port 8000

# Enable debug logging
export PYTHONPATH=.
python -c "
import logging
from src.utils import setup_logging
setup_logging('src', level=logging.DEBUG)
from src import server
server.main()
"
```

## Debugging

### Enabling Debug Logging

Debug logging provides detailed information about API calls, retries, and errors.

**Method 1: Environment Variable**
```bash
export LOG_LEVEL=DEBUG
python -m src.server
```

**Method 2: Code Modification**
In `src/utils.py`, change default level:
```python
def setup_logging(name: str, level: int = logging.DEBUG):  # Changed from INFO
    # ...
```

### Common Debugging Scenarios

#### 1. API Authentication Issues

**Symptoms:**
- `AuthenticationError: Authentication failed (HTTP 401)`
- Immediate failures on startup

**Debugging:**
```bash
# Verify token is set
echo $TESSIE_TOKEN

# Test token manually
curl -H "Authorization: Bearer $TESSIE_TOKEN" \
  https://api.tessie.com/vehicles

# Check logs for token issues
grep -i "auth" tessie_mcp.log
```

**Solutions:**
- Verify `TESSIE_TOKEN` in `.env`
- Ensure token hasn't expired
- Check token has required permissions

#### 2. Vehicle Not Found

**Symptoms:**
- `VehicleNotFoundError: Vehicle with VIN '5YJ3E****3456' not found`

**Debugging:**
```bash
# List all vehicles
curl -H "Authorization: Bearer $TESSIE_TOKEN" \
  https://api.tessie.com/vehicles | jq

# Verify VIN format (17 characters, alphanumeric)
python -c "from src.utils import validate_vin; print(validate_vin('YOUR_VIN'))"
```

**Solutions:**
- Verify `VEHICLE_VIN` in `.env` matches exactly
- Check vehicle is associated with your Tessie account
- Ensure no extra spaces or characters

#### 3. Rate Limiting

**Symptoms:**
- `TessieAPIError: Rate limit exceeded (HTTP 429)`
- Retries exhausted

**Debugging:**
```bash
# Check retry configuration
grep -E "MAX_API_RETRIES|RETRY_BACKOFF" src/constants.py

# Monitor retry attempts
grep "Rate limited" tessie_mcp.log
```

**Solutions:**
- Increase `TELEMETRY_INTERVAL` to reduce API calls
- Wait before retrying
- Contact Tessie support for rate limit increase

#### 4. Stale Data Issues

**Symptoms:**
- Data appears old or inconsistent
- Timestamps don't match current time

**Debugging:**
```python
# Check cache age
from src.telemetry.service import Telemetry
tel = Telemetry(vin="YOUR_VIN", interval=5)

# Force refresh
tel._cache = None
tel._cache_time = None
data = tel._fetch_data()
print(data)
```

**Solutions:**
- Set `TELEMETRY_INTERVAL=realtime` in `.env`
- Check vehicle is awake (use `get_vehicle_status`)
- Verify network connectivity

### Logging Output Analysis

**Key Log Patterns:**

```
# Successful API call
2025-11-29 10:15:30 - src.tessie_client - INFO - Fetching battery data for VIN 5YJ3E****3456
2025-11-29 10:15:31 - src.tessie_client - DEBUG - Making GET request to https://... (attempt 1/4)
2025-11-29 10:15:32 - src.tessie_client - DEBUG - Response status: 200
2025-11-29 10:15:32 - src.tessie_client - DEBUG - Request successful, received 1234 bytes

# Rate limit with retry
2025-11-29 10:15:35 - src.tessie_client - WARNING - Rate limited. Waiting 2s before retry...
2025-11-29 10:15:37 - src.tessie_client - DEBUG - Making GET request to https://... (attempt 2/4)

# Error
2025-11-29 10:15:40 - src.tessie_client - ERROR - Request failed: Connection timeout
```

## Testing

### Manual Testing

```bash
# Test individual components
python -c "
from src.tessie_client import TessieClient
client = TessieClient()

# Test vehicle discovery
vehicles = client.fetch_vehicles()
print(f'Found {len(vehicles)} vehicle(s)')

# Test battery endpoint
vin = 'YOUR_VIN'
battery = client.get_battery(vin)
print(f'Battery: {battery[\"battery_level\"]}%')
"
```

### Testing MCP Tools

```bash
# Start server in STDIO mode
python -m src.server

# In another terminal, send MCP commands
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m src.server

# Test specific tool
echo '{
  "jsonrpc":"2.0",
  "id":2,
  "method":"tools/call",
  "params":{
    "name":"get_battery_information",
    "arguments":{}
  }
}' | python -m src.server
```

## Adding New Features

### Adding a New Telemetry Endpoint

**Example: Adding odometer reading**

1. **Add endpoint constant** (`src/constants.py`):
   ```python
   ENDPOINT_ODOMETER = "/{vin}/odometer"
   ```

2. **Add client method** (`src/tessie_client.py`):
   ```python
   def get_odometer(self, vin: str) -> Dict[str, Any]:
       """Get odometer reading for a vehicle."""
       sanitized_vin = sanitize_vin_for_logging(vin)
       self.logger.info("Fetching odometer for VIN %s", sanitized_vin)

       url = f"{self.base_url}{ENDPOINT_ODOMETER.format(vin=vin)}"
       return self._make_request("GET", url)
   ```

3. **Add service method** (`src/telemetry/service.py`):
   ```python
   def get_odometer_reading(self) -> str:
       """Get formatted odometer reading."""
       data = self.client.get_odometer(self.vin)
       odometer = data.get("odometer", 0)
       return f"Odometer: {odometer:,} miles"
   ```

4. **Register tool** (`src/telemetry/tools.py`):
   ```python
   TELEMETRY_TOOL_SPECS: list[tuple[str, str]] = [
       ("get_odometer_reading", "Get the vehicle's odometer reading in miles"),
       # ... existing tools
   ]
   ```

5. **Test the new tool**:
   ```bash
   python -c "
   from src.telemetry.service import Telemetry
   tel = Telemetry(vin='YOUR_VIN')
   print(tel.get_odometer_reading())
   "
   ```

### Adding a New Control Command

**Example: Adding door lock command**

1. **Add endpoint constant** (`src/constants.py`):
   ```python
   ENDPOINT_COMMAND_LOCK = "/{vin}/command/lock"
   ```

2. **Add client method** (`src/tessie_client.py`):
   ```python
   def lock_doors(self, vin: str) -> Dict[str, Any]:
       """Lock the vehicle doors."""
       sanitized_vin = sanitize_vin_for_logging(vin)
       self.logger.info("Sending lock command to VIN %s", sanitized_vin)

       url = f"{self.base_url}{ENDPOINT_COMMAND_LOCK.format(vin=vin)}"
       return self._make_request("POST", url)
   ```

3. **Update service method** (`src/control/service.py`):
   ```python
   def lock_doors(self) -> str:
       """Lock the vehicle doors."""
       try:
           response = self.client.lock_doors(self.vin)
           result = response.get("result", False)

           if result:
               return "Successfully locked doors!"
           else:
               error = response.get("reason", "Unknown error")
               raise VehicleCommandError("lock_doors", error, self.vin)

       except Exception as e:
           self.logger.error("Failed to lock doors: %s", str(e))
           return f"Error locking doors: {str(e)}"
   ```

4. **Tool is already registered** in `src/control/tools.py`

## Error Handling

### Exception Hierarchy

```
TessieMCPError (base)
├── VehicleNotFoundError
├── TessieAPIError
├── AuthenticationError
├── ConfigurationError
├── VehicleCommandError
└── DataValidationError
```

### Best Practices

**1. Use Specific Exceptions**
```python
# Good
if not vehicle:
    raise VehicleNotFoundError(vin)

# Bad
if not vehicle:
    raise Exception(f"Vehicle {vin} not found")
```

**2. Provide Context**
```python
# Good
raise VehicleCommandError("honk_horn", "Vehicle is asleep", vin)

# Bad
raise Exception("Command failed")
```

**3. Log Before Raising**
```python
try:
    result = dangerous_operation()
except SomeError as e:
    self.logger.error("Operation failed: %s", str(e), exc_info=True)
    raise  # Re-raise with full context
```

## Logging

### Log Levels

- **DEBUG**: Detailed diagnostic information (API calls, retries, data parsing)
- **INFO**: General informational messages (server started, vehicle found)
- **WARNING**: Warning messages (rate limits, stale data, invalid VIN format)
- **ERROR**: Error messages (API failures, command failures)
- **CRITICAL**: Critical failures (server crash, unrecoverable errors)

### Logging Guidelines

**1. Use Structured Logging**
```python
# Good
self.logger.info("Fetching battery for VIN %s", sanitized_vin)

# Bad
self.logger.info(f"Fetching battery for VIN {sanitized_vin}")
```

**2. Sanitize Sensitive Data**
```python
# Always sanitize VINs
sanitized_vin = sanitize_vin_for_logging(vin)
self.logger.info("Processing VIN %s", sanitized_vin)

# Never log full tokens
# BAD: self.logger.debug(f"Token: {self.token}")
```

**3. Log at Appropriate Levels**
```python
self.logger.debug("Cache hit for VIN %s", vin)  # Diagnostic
self.logger.info("Vehicle found: %s", name)      # Informational
self.logger.warning("Data is %d minutes old", age)  # Warning
self.logger.error("API call failed: %s", error)   # Error
```

## Best Practices

### 1. Always Use Type Hints
```python
def get_battery(self, vin: str) -> Dict[str, Any]:
    # ...
```

### 2. Validate Inputs
```python
if not validate_vin(vin):
    raise ValueError(f"Invalid VIN format: {vin}")
```

### 3. Use Constants
```python
# Good
if temp < HEATER_OFF:

# Bad
if temp < 0:
```

### 4. Write Descriptive Docstrings
```python
def complex_function(param: str) -> int:
    """One-line summary.

    Detailed explanation of what this function does,
    including any important caveats or edge cases.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param is invalid

    Example:
        >>> result = complex_function("test")
        >>> print(result)
        42
    """
```

### 5. Handle Errors Gracefully
```python
try:
    result = api_call()
except TessieAPIError as e:
    self.logger.error("API call failed: %s", str(e))
    return "Service temporarily unavailable"
```

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings for all public methods
- Keep functions focused and small
- Use meaningful variable names

### Commit Messages
```
feat: add odometer reading endpoint
fix: handle timeout errors in battery fetch
docs: update development guide with testing
refactor: extract formatting into utils
```

### Pull Request Process
1. Create feature branch: `git checkout -b feature/new-endpoint`
2. Make changes with tests
3. Update documentation
4. Submit PR with clear description
5. Address review feedback

## Troubleshooting

### Server Won't Start

**Check:**
- Virtual environment activated?
- Dependencies installed? (`pip install -r requirements.txt`)
- `.env` file exists with required variables?
- Python version 3.10+?

### MCP Client Can't Connect

**Check:**
- Server running in correct mode (STDIO vs SSE)?
- Correct port for SSE mode?
- Firewall blocking connections?
- Client configured with correct server path?

### Data Always Stale

**Check:**
- `TELEMETRY_INTERVAL` setting
- Vehicle is awake (check with `get_vehicle_status`)
- Cache is being invalidated properly

## Additional Resources

- [Tessie API Documentation](https://developer.tessie.com)
- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Project Issues](https://github.com/your-repo/issues)

---

For questions or issues, please file a GitHub issue or contact the maintainers.
