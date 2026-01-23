"""Telemetry tool definitions and dispatch helpers."""

from typing import Callable

from mcp.types import Tool

from .service import Telemetry


TELEMETRY_TOOL_SPECS: list[tuple[str, str]] = [
    # New efficient specialized endpoint tools
    ("get_battery_information", "Get detailed battery information (level, drain, energy, voltage, current, temperature) using efficient /battery endpoint"),
    ("get_battery_health_information", "Get battery health information (max range, capacity, degradation) using /battery_health endpoint"),
    ("get_location_information", "Get vehicle location with address and saved location name using /location endpoint"),
    ("get_tire_pressure_information", "Get tire pressure for all four tires with status indicators using /tire_pressure endpoint"),
    ("get_vehicle_status", "Get vehicle sleep/wake status (asleep, waiting_for_sleep, or awake) using /status endpoint"),
    # Legacy tools (still functional but less efficient)
    ("get_in_service", "Check if the vehicle is in service mode (used during maintenance/repairs)"),
    ("get_battery_heater_on", "Check if the battery heater is active (warms battery for optimal charging in cold weather)"),
    ("get_battery_level", "Get the current battery level as a percentage"),
    ("get_charge_limit_soc", "Get the charging limit percentage (100% means no limit set)"),
    ("get_charge_port_door_open", "Check if the charge port door is open or closed"),
    ("get_charging_state", "Get the current charging status (Charging, Complete, Disconnected, etc.)"),
    ("get_minutes_to_full_charge", "Get the estimated time remaining until charging is complete"),
    ("get_charging_complete_at", "Get the estimated date and time when charging will be complete"),
    ("get_energy_remaining", "Get the remaining battery energy in kilowatt-hours (kWh)"),
    ("get_lifetime_energy_used", "Get the total energy consumed by the vehicle over its lifetime in kWh"),
    ("get_allow_cabin_overheat_protection", "Check if Cabin Overheat Protection (COP) is enabled"),
    ("get_outside_temp", "Get the outside ambient temperature in Celsius"),
    ("get_is_climate_on", "Check if the climate control (HVAC) is currently active"),
    ("get_supports_fan_only_cabin_overheat_protection", "Check if vehicle supports fan-only Cabin Overheat Protection (uses less energy than AC)"),
    ("get_seat_heater_left", "Get the driver (left front) seat heater status and level"),
    ("get_seat_heater_right", "Get the passenger (right front) seat heater status and level"),
    ("get_seat_heater_rear_left", "Get the rear left seat heater status and level"),
    ("get_seat_heater_rear_center", "Get the rear center seat heater status and level"),
    ("get_seat_heater_rear_right", "Get the rear right seat heater status and level"),
    ("get_side_mirror_heaters", "Check if the side mirror heaters are active"),
    ("get_steering_wheel_heater", "Get the steering wheel heater status and level"),
    ("get_wiper_blade_heater", "Check if the windshield wiper blade heater is active"),
    ("get_location", "Get the vehicle's current GPS location and heading direction"),
    ("get_power", "Get the current power usage or regeneration in kilowatts"),
    ("get_speed", "Get the vehicle's current speed"),
    ("get_shift_state", "Get the current gear (Park, Reverse, Neutral, Drive)"),
    ("get_active_route", "Get information about the active navigation route (destination, ETA, distance, battery at arrival)"),
    ("get_sentry_mode", "Check if Sentry Mode is active (security camera monitoring)"),
    ("get_display_name", "Get the vehicle's custom display name"),
    ("get_all_heater_status", "Get a summary of all heater statuses (seats, steering wheel, mirrors, wipers)"),
    ("get_battery_summary", "Get a comprehensive battery and charging summary"),
]

TELEMETRY_TOOLS: list[Tool] = [
    Tool(
        name=name,
        description=description,
        inputSchema={"type": "object", "properties": {}, "required": []},
    )
    for name, description in TELEMETRY_TOOL_SPECS
]


def build_telemetry_dispatch(telemetry: Telemetry) -> dict[str, Callable[[dict], str]]:
    """Build a mapping of telemetry tool names to bound methods."""
    dispatch: dict[str, Callable[[dict], str]] = {}
    for name, _ in TELEMETRY_TOOL_SPECS:
        method = getattr(telemetry, name, None)
        if method is None:
            raise AttributeError(f"Telemetry missing expected method {name}")
        dispatch[name] = lambda _args=None, method=method: method()
    return dispatch


__all__ = ["TELEMETRY_TOOLS", "TELEMETRY_TOOL_SPECS", "build_telemetry_dispatch"]
