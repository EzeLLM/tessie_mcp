"""Constants and configuration values for the Tessie MCP server.

This module centralizes all magic numbers, default values, and configuration
constants used throughout the application.
"""

# API Configuration
TESSIE_BASE_URL = "https://api.tessie.com"
DEFAULT_API_TIMEOUT = 30  # seconds
MAX_API_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # exponential backoff multiplier

# HTTP Status Codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429
HTTP_SERVER_ERROR = 500

# Telemetry Configuration
DEFAULT_TELEMETRY_INTERVAL = 5  # minutes
REALTIME_MODE = "realtime"

# Heater Levels
HEATER_OFF = 0
HEATER_LOW = 1
HEATER_MEDIUM = 2
HEATER_HIGH = 3

HEATER_LEVEL_NAMES = {
    HEATER_OFF: "off",
    HEATER_LOW: "low",
    HEATER_MEDIUM: "medium",
    HEATER_HIGH: "high",
}

# Shift States
SHIFT_PARK = "P"
SHIFT_REVERSE = "R"
SHIFT_NEUTRAL = "N"
SHIFT_DRIVE = "D"

SHIFT_STATE_NAMES = {
    SHIFT_PARK: "Park",
    SHIFT_REVERSE: "Reverse",
    SHIFT_NEUTRAL: "Neutral",
    SHIFT_DRIVE: "Drive",
}

# Charging States
CHARGING_STATE_CHARGING = "Charging"
CHARGING_STATE_COMPLETE = "Complete"
CHARGING_STATE_DISCONNECTED = "Disconnected"
CHARGING_STATE_STOPPED = "Stopped"
CHARGING_STATE_STARTING = "Starting"
CHARGING_STATE_NO_POWER = "NoPower"

# Vehicle Status
STATUS_ASLEEP = "asleep"
STATUS_WAITING_FOR_SLEEP = "waiting_for_sleep"
STATUS_AWAKE = "awake"

# Compass Directions (for heading conversion)
COMPASS_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
DEGREES_PER_DIRECTION = 45

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Environment Variables
ENV_TESSIE_TOKEN = "TESSIE_TOKEN"
ENV_VEHICLE_VIN = "VEHICLE_VIN"
ENV_TELEMETRY_INTERVAL = "TELEMETRY_INTERVAL"

# MCP Server Configuration
MCP_SERVER_NAME = "tessie-mcp"
DEFAULT_SSE_HOST = "0.0.0.0"
DEFAULT_SSE_PORT = 8000

# API Endpoints (relative to base URL)
ENDPOINT_VEHICLES = "/vehicles"
ENDPOINT_BATTERY = "/{vin}/battery"
ENDPOINT_BATTERY_HEALTH = "/{vin}/battery_health"
ENDPOINT_LOCATION = "/{vin}/location"
ENDPOINT_TIRE_PRESSURE = "/{vin}/tire_pressure"
ENDPOINT_STATUS = "/{vin}/status"
ENDPOINT_COMMAND_HONK = "/{vin}/command/honk"
ENDPOINT_COMMAND_FLASH = "/{vin}/command/flash"

# Data Validation Thresholds
MIN_BATTERY_LEVEL = 0
MAX_BATTERY_LEVEL = 100
MIN_TIRE_PRESSURE = 0.0  # bar
MAX_TIRE_PRESSURE = 5.0  # bar
MAX_DATA_AGE_HOURS = 24  # warn if data is older than this
