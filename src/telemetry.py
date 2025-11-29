"""Tesla vehicle telemetry data retrieval and formatting."""

import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from dotenv import load_dotenv

from .tessie_client import TessieClient

# Load .env from project root for standalone usage
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Telemetry:
    """Tesla vehicle telemetry data handler with intelligent caching.
    
    Retrieves and formats vehicle data from the Tessie API with configurable
    refresh intervals. Each data field has a private method returning raw values
    and a public method returning human-readable formatted strings.
    
    Attributes:
        interval: Data refresh interval in minutes, or 'realtime' for always fresh.
    """
    
    # Heater level mappings
    _HEATER_LEVELS = {0: "off", 1: "low", 2: "medium", 3: "high"}
    
    def __init__(
        self,
        plate: str,
        interval: Union[int, str] = 5,
        client: Optional[TessieClient] = None
    ):
        """Initialize the Telemetry handler.
        
        Args:
            plate: Vehicle license plate to retrieve data for.
            interval: Data refresh interval in minutes. Use 'realtime' to always
                     fetch fresh data. Defaults to 5 minutes.
            client: Optional TessieClient instance. Creates one if not provided.
        """
        self.plate = plate
        self.interval = interval
        self.client = client or TessieClient()
        
        self._cache: Optional[dict] = None
        self._cache_time: Optional[float] = None
        self._lock = threading.Lock()
    
    def _should_refresh(self) -> bool:
        """Check if cached data should be refreshed.
        
        Returns:
            True if data needs refreshing, False otherwise.
        """
        if self.interval == "realtime":
            return True
        
        if self._cache is None or self._cache_time is None:
            return True
        
        elapsed_minutes = (time.time() - self._cache_time) / 60
        return elapsed_minutes > self.interval
    
    def _fetch_data(self) -> dict:
        """Fetch fresh vehicle data from the API.
        
        Returns:
            Vehicle state dictionary.
        
        Raises:
            ValueError: If vehicle with specified plate is not found.
        """
        with self._lock:
            if not self._should_refresh() and self._cache is not None:
                return self._cache
            
            state = self.client.get_vehicle_state(self.plate)
            
            if state is None:
                raise ValueError(f"Vehicle with plate '{self.plate}' not found")
            
            self._cache = state
            self._cache_time = time.time()
            
            return self._cache
    
    def _get_nested(self, *keys: str, default: Any = None) -> Any:
        """Get a nested value from cached vehicle data.
        
        Args:
            *keys: Path of keys to traverse (e.g., 'charge_state', 'battery_level').
            default: Default value if path not found.
        
        Returns:
            The value at the specified path, or default if not found.
        """
        data = self._fetch_data()
        
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        
        return data
    
    @staticmethod
    def _heater_level_str(level: int) -> str:
        """Convert heater level number to descriptive string.
        
        Args:
            level: Heater level (0-3).
        
        Returns:
            Descriptive string (off/low/medium/high).
        """
        return Telemetry._HEATER_LEVELS.get(level, "unknown")
    
    # =========================================================================
    # SERVICE STATUS
    # =========================================================================
    
    def _get_in_service(self) -> bool:
        """Get raw service mode status.
        
        Returns:
            True if vehicle is in service mode, False otherwise.
        """
        return self._get_nested("in_service", default=False)
    
    def get_in_service(self) -> str:
        """Get formatted service mode status.
        
        Indicates whether the vehicle is currently in service mode, which is
        used by technicians during maintenance or repairs.
        
        Returns:
            Human-readable service mode status.
        """
        in_service = self._get_in_service()
        if in_service:
            return "Vehicle is in service mode"
        return "Vehicle is not in service mode"
    
    # =========================================================================
    # BATTERY & CHARGING
    # =========================================================================
    
    def _get_battery_heater_on(self) -> bool:
        """Get raw battery heater status.
        
        Returns:
            True if battery heater is active, False otherwise.
        """
        return self._get_nested("charge_state", "battery_heater_on", default=False)
    
    def get_battery_heater_on(self) -> str:
        """Get formatted battery heater status.
        
        The battery heater warms the battery pack in cold weather to improve
        charging speed and efficiency.
        
        Returns:
            Human-readable battery heater status.
        """
        heater_on = self._get_battery_heater_on()
        if heater_on:
            return "Battery heater is active (warming battery for optimal charging)"
        return "Battery heater is off"
    
    def _get_battery_level(self) -> int:
        """Get raw battery level percentage.
        
        Returns:
            Battery level as percentage (0-100).
        """
        return self._get_nested("charge_state", "battery_level", default=0)
    
    def get_battery_level(self) -> str:
        """Get formatted battery level.
        
        Reports the current state of charge of the vehicle's battery pack
        as a percentage.
        
        Returns:
            Human-readable battery level.
        """
        level = self._get_battery_level()
        return f"Battery is at {level}%"
    
    def _get_charge_limit_soc(self) -> int:
        """Get raw charge limit percentage.
        
        Returns:
            Charge limit as percentage (50-100).
        """
        return self._get_nested("charge_state", "charge_limit_soc", default=80)
    
    def get_charge_limit_soc(self) -> str:
        """Get formatted charge limit.
        
        Reports the maximum charge level the vehicle will charge to. A limit
        of 100% means no limit is set and the battery will charge fully.
        
        Returns:
            Human-readable charge limit.
        """
        limit = self._get_charge_limit_soc()
        if limit == 100:
            return "Charge limit is set to 100% (full charge, no limit)"
        return f"Charge limit is set to {limit}%"
    
    def _get_charge_port_door_open(self) -> bool:
        """Get raw charge port door status.
        
        Returns:
            True if charge port door is open, False otherwise.
        """
        return self._get_nested("charge_state", "charge_port_door_open", default=False)
    
    def get_charge_port_door_open(self) -> str:
        """Get formatted charge port door status.
        
        Reports whether the vehicle's charge port door is currently open or closed.
        
        Returns:
            Human-readable charge port door status.
        """
        is_open = self._get_charge_port_door_open()
        if is_open:
            return "Charge port door is open"
        return "Charge port door is closed"
    
    def _get_charging_state(self) -> str:
        """Get raw charging state.
        
        Returns:
            Charging state string (e.g., 'Charging', 'Complete', 'Disconnected').
        """
        return self._get_nested("charge_state", "charging_state", default="Unknown")
    
    def get_charging_state(self) -> str:
        """Get formatted charging state.
        
        Reports the current charging status of the vehicle.
        
        Returns:
            Human-readable charging state.
        """
        state = self._get_charging_state()
        state_messages = {
            "Charging": "Vehicle is currently charging",
            "Complete": "Charging is complete",
            "Disconnected": "Vehicle is not connected to a charger",
            "Stopped": "Charging has been stopped",
            "Starting": "Charging is starting",
            "NoPower": "Charger connected but no power available",
        }
        return state_messages.get(state, f"Charging state: {state}")
    
    def _get_minutes_to_full_charge(self) -> int:
        """Get raw minutes until charging complete.
        
        Returns:
            Minutes remaining until charge limit reached.
        """
        return self._get_nested("charge_state", "minutes_to_full_charge", default=0)
    
    def get_minutes_to_full_charge(self) -> str:
        """Get formatted time to full charge.
        
        Reports how many minutes remain until the vehicle reaches its charge limit.
        
        Returns:
            Human-readable time to full charge.
        """
        minutes = self._get_minutes_to_full_charge()
        if minutes == 0:
            return "Vehicle is not actively charging or is fully charged"
        
        hours = minutes // 60
        remaining_mins = minutes % 60
        
        if hours > 0:
            return f"Charging will complete in {hours}h {remaining_mins}m"
        return f"Charging will complete in {minutes} minutes"
    
    def _get_charging_complete_at(self) -> Optional[datetime]:
        """Get estimated charging completion datetime.
        
        Returns:
            Datetime when charging will complete, or None if not charging.
        """
        minutes = self._get_minutes_to_full_charge()
        if minutes == 0:
            return None
        return datetime.now() + timedelta(minutes=minutes)
    
    def get_charging_complete_at(self) -> str:
        """Get formatted charging completion time.
        
        Calculates and reports the estimated date and time when charging will
        be complete based on the current charge rate.
        
        Returns:
            Human-readable charging completion time.
        """
        complete_time = self._get_charging_complete_at()
        if complete_time is None:
            return "Vehicle is not actively charging"
        return f"Charging will complete at {complete_time.strftime('%Y-%m-%d %H:%M')}"
    
    def _get_energy_remaining(self) -> float:
        """Get raw remaining battery energy in kWh.
        
        Returns:
            Remaining energy in kilowatt-hours.
        """
        return self._get_nested("charge_state", "energy_remaining", default=0.0)
    
    def get_energy_remaining(self) -> str:
        """Get formatted remaining battery energy.
        
        Reports the actual energy remaining in the battery pack in kilowatt-hours.
        
        Returns:
            Human-readable remaining energy.
        """
        energy = self._get_energy_remaining()
        return f"Battery has {energy:.2f} kWh remaining"
    
    def _get_lifetime_energy_used(self) -> float:
        """Get raw lifetime energy consumption in kWh.
        
        Returns:
            Total energy consumed since vehicle production in kWh.
        """
        return self._get_nested("charge_state", "lifetime_energy_used", default=0.0)
    
    def get_lifetime_energy_used(self) -> str:
        """Get formatted lifetime energy consumption.
        
        Reports the total energy that has been fed to the vehicle over its lifetime.
        
        Returns:
            Human-readable lifetime energy consumption.
        """
        energy = self._get_lifetime_energy_used()
        return f"Vehicle has consumed {energy:.2f} kWh in its lifetime"
    
    # =========================================================================
    # CLIMATE & TEMPERATURE
    # =========================================================================
    
    def _get_allow_cabin_overheat_protection(self) -> bool:
        """Get raw cabin overheat protection setting.
        
        Returns:
            True if cabin overheat protection is enabled, False otherwise.
        """
        return self._get_nested(
            "climate_state", "allow_cabin_overheat_protection", default=False
        )
    
    def get_allow_cabin_overheat_protection(self) -> str:
        """Get formatted cabin overheat protection status.
        
        Cabin Overheat Protection (COP) prevents the interior from getting too hot
        by automatically activating climate control when parked.
        
        Returns:
            Human-readable cabin overheat protection status.
        """
        enabled = self._get_allow_cabin_overheat_protection()
        if enabled:
            return "Cabin Overheat Protection is enabled"
        return "Cabin Overheat Protection is disabled"
    
    def _get_outside_temp(self) -> float:
        """Get raw outside temperature in Celsius.
        
        Returns:
            Outside temperature in degrees Celsius.
        """
        return self._get_nested("climate_state", "outside_temp", default=0.0)
    
    def get_outside_temp(self) -> str:
        """Get formatted outside temperature.
        
        Reports the ambient temperature outside the vehicle as measured by
        onboard sensors.
        
        Returns:
            Human-readable outside temperature.
        """
        temp = self._get_outside_temp()
        return f"Outside temperature is {temp}°C"
    
    def _get_is_climate_on(self) -> bool:
        """Get raw climate control status.
        
        Returns:
            True if climate control is active, False otherwise.
        """
        return self._get_nested("climate_state", "is_climate_on", default=False)
    
    def get_is_climate_on(self) -> str:
        """Get formatted climate control status.
        
        Reports whether the vehicle's HVAC system is currently running.
        
        Returns:
            Human-readable climate control status.
        """
        is_on = self._get_is_climate_on()
        if is_on:
            return "Climate control is active"
        return "Climate control is off"
    
    def _get_supports_fan_only_cabin_overheat_protection(self) -> bool:
        """Get raw fan-only COP capability.
        
        Returns:
            True if vehicle supports fan-only cabin overheat protection.
        """
        return self._get_nested(
            "climate_state",
            "supports_fan_only_cabin_overheat_protection",
            default=False
        )
    
    def get_supports_fan_only_cabin_overheat_protection(self) -> str:
        """Get formatted fan-only COP capability.
        
        Reports whether the vehicle can protect the cabin from overheating
        using only fans (without AC), which uses less energy.
        
        Returns:
            Human-readable fan-only COP capability status.
        """
        supported = self._get_supports_fan_only_cabin_overheat_protection()
        if supported:
            return "Vehicle supports fan-only Cabin Overheat Protection"
        return "Vehicle requires AC for Cabin Overheat Protection"
    
    # =========================================================================
    # SEAT HEATERS
    # =========================================================================
    
    def _get_seat_heater_left(self) -> int:
        """Get raw driver (left) seat heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested("climate_state", "seat_heater_left", default=0)
    
    def get_seat_heater_left(self) -> str:
        """Get formatted driver seat heater status.
        
        Reports the heating level of the driver's (left front) seat.
        
        Returns:
            Human-readable driver seat heater status.
        """
        level = self._get_seat_heater_left()
        level_str = self._heater_level_str(level)
        return f"Driver seat heater is {level_str}"
    
    def _get_seat_heater_right(self) -> int:
        """Get raw passenger (right) seat heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested("climate_state", "seat_heater_right", default=0)
    
    def get_seat_heater_right(self) -> str:
        """Get formatted passenger seat heater status.
        
        Reports the heating level of the front passenger's (right front) seat.
        
        Returns:
            Human-readable passenger seat heater status.
        """
        level = self._get_seat_heater_right()
        level_str = self._heater_level_str(level)
        return f"Passenger seat heater is {level_str}"
    
    def _get_seat_heater_rear_left(self) -> int:
        """Get raw rear left seat heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested("climate_state", "seat_heater_rear_left", default=0)
    
    def get_seat_heater_rear_left(self) -> str:
        """Get formatted rear left seat heater status.
        
        Reports the heating level of the rear left seat.
        
        Returns:
            Human-readable rear left seat heater status.
        """
        level = self._get_seat_heater_rear_left()
        level_str = self._heater_level_str(level)
        return f"Rear left seat heater is {level_str}"
    
    def _get_seat_heater_rear_center(self) -> int:
        """Get raw rear center seat heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested("climate_state", "seat_heater_rear_center", default=0)
    
    def get_seat_heater_rear_center(self) -> str:
        """Get formatted rear center seat heater status.
        
        Reports the heating level of the rear center seat.
        
        Returns:
            Human-readable rear center seat heater status.
        """
        level = self._get_seat_heater_rear_center()
        level_str = self._heater_level_str(level)
        return f"Rear center seat heater is {level_str}"
    
    def _get_seat_heater_rear_right(self) -> int:
        """Get raw rear right seat heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested("climate_state", "seat_heater_rear_right", default=0)
    
    def get_seat_heater_rear_right(self) -> str:
        """Get formatted rear right seat heater status.
        
        Reports the heating level of the rear right seat.
        
        Returns:
            Human-readable rear right seat heater status.
        """
        level = self._get_seat_heater_rear_right()
        level_str = self._heater_level_str(level)
        return f"Rear right seat heater is {level_str}"
    
    # =========================================================================
    # OTHER HEATERS
    # =========================================================================
    
    def _get_side_mirror_heaters(self) -> bool:
        """Get raw side mirror heaters status.
        
        Returns:
            True if side mirror heaters are active, False otherwise.
        """
        return self._get_nested("climate_state", "side_mirror_heaters", default=False)
    
    def get_side_mirror_heaters(self) -> str:
        """Get formatted side mirror heaters status.
        
        Reports whether the side mirror heaters are currently active.
        
        Returns:
            Human-readable side mirror heaters status.
        """
        is_on = self._get_side_mirror_heaters()
        if is_on:
            return "Side mirror heaters are active"
        return "Side mirror heaters are off"
    
    def _get_steering_wheel_heater(self) -> bool:
        """Get raw steering wheel heater on/off status.
        
        Returns:
            True if steering wheel heater is enabled, False otherwise.
        """
        return self._get_nested("climate_state", "steering_wheel_heater", default=False)
    
    def _get_steering_wheel_heat_level(self) -> int:
        """Get raw steering wheel heater level.
        
        Returns:
            Heater level (0=off, 1=low, 2=medium, 3=high).
        """
        return self._get_nested(
            "climate_state", "steering_wheel_heat_level", default=0
        )
    
    def get_steering_wheel_heater(self) -> str:
        """Get formatted steering wheel heater status.
        
        Reports whether the steering wheel heater is active and at what level.
        
        Returns:
            Human-readable steering wheel heater status.
        """
        is_on = self._get_steering_wheel_heater()
        if not is_on:
            return "Steering wheel heater is off"
        
        level = self._get_steering_wheel_heat_level()
        level_str = self._heater_level_str(level)
        return f"Steering wheel heater is on ({level_str})"
    
    def _get_wiper_blade_heater(self) -> bool:
        """Get raw wiper blade heater status.
        
        Returns:
            True if wiper blade heater is active, False otherwise.
        """
        return self._get_nested("climate_state", "wiper_blade_heater", default=False)
    
    def get_wiper_blade_heater(self) -> str:
        """Get formatted wiper blade heater status.
        
        Reports whether the windshield wiper blade heater is currently active.
        
        Returns:
            Human-readable wiper blade heater status.
        """
        is_on = self._get_wiper_blade_heater()
        if is_on:
            return "Wiper blade heater is active"
        return "Wiper blade heater is off"
    
    # =========================================================================
    # DRIVE STATE & LOCATION
    # =========================================================================
    
    def _get_latitude(self) -> float:
        """Get raw GPS latitude.
        
        Returns:
            Latitude in decimal degrees.
        """
        return self._get_nested("drive_state", "latitude", default=0.0)
    
    def _get_longitude(self) -> float:
        """Get raw GPS longitude.
        
        Returns:
            Longitude in decimal degrees.
        """
        return self._get_nested("drive_state", "longitude", default=0.0)
    
    def _get_heading(self) -> int:
        """Get raw compass heading.
        
        Returns:
            Heading in degrees (0-359, where 0 is North).
        """
        return self._get_nested("drive_state", "heading", default=0)
    
    def get_location(self) -> str:
        """Get formatted vehicle location.
        
        Reports the current GPS coordinates and compass heading of the vehicle.
        
        Returns:
            Human-readable vehicle location.
        """
        lat = self._get_latitude()
        lon = self._get_longitude()
        heading = self._get_heading()
        
        # Convert heading to cardinal direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(heading / 45) % 8
        cardinal = directions[idx]
        
        return f"Vehicle is at {lat:.6f}, {lon:.6f} facing {cardinal} ({heading}°)"
    
    def _get_power(self) -> int:
        """Get raw power usage in kW.
        
        Returns:
            Current power draw in kilowatts (negative = regenerating).
        """
        return self._get_nested("drive_state", "power", default=0)
    
    def get_power(self) -> str:
        """Get formatted power usage.
        
        Reports the current power draw or regeneration of the vehicle in kilowatts.
        
        Returns:
            Human-readable power usage.
        """
        power = self._get_power()
        if power == 0:
            return "Vehicle is idle (0 kW)"
        elif power > 0:
            return f"Vehicle is using {power} kW"
        else:
            return f"Vehicle is regenerating {abs(power)} kW"
    
    def _get_speed(self) -> Optional[int]:
        """Get raw vehicle speed.
        
        Returns:
            Speed in mph, or None if stationary.
        """
        return self._get_nested("drive_state", "speed", default=None)
    
    def get_speed(self) -> str:
        """Get formatted vehicle speed.
        
        Reports the current speed of the vehicle.
        
        Returns:
            Human-readable vehicle speed.
        """
        speed = self._get_speed()
        if speed is None or speed == 0:
            return "Vehicle is stationary"
        return f"Vehicle is moving at {speed} mph"
    
    def _get_shift_state(self) -> Optional[str]:
        """Get raw gear shift state.
        
        Returns:
            Shift state (P/R/N/D) or None.
        """
        return self._get_nested("drive_state", "shift_state", default="P")
    
    def get_shift_state(self) -> str:
        """Get formatted gear shift state.
        
        Reports which gear the vehicle is currently in.
        
        Returns:
            Human-readable shift state.
        """
        state = self._get_shift_state()
        state_names = {
            "P": "Park",
            "R": "Reverse",
            "N": "Neutral",
            "D": "Drive",
        }
        name = state_names.get(state, state or "Unknown")
        return f"Vehicle is in {name}"
    
    # =========================================================================
    # ACTIVE ROUTE
    # =========================================================================
    
    def _get_active_route_destination(self) -> Optional[str]:
        """Get raw active route destination.
        
        Returns:
            Destination name, or None if no active route.
        """
        return self._get_nested("drive_state", "active_route_destination", default=None)
    
    def _get_active_route_minutes_to_arrival(self) -> Optional[float]:
        """Get raw minutes to arrival for active route.
        
        Returns:
            Minutes until arrival, or None if no active route.
        """
        return self._get_nested(
            "drive_state", "active_route_minutes_to_arrival", default=None
        )
    
    def _get_active_route_miles_to_arrival(self) -> Optional[float]:
        """Get raw miles to arrival for active route.
        
        Returns:
            Miles until arrival, or None if no active route.
        """
        return self._get_nested(
            "drive_state", "active_route_miles_to_arrival", default=None
        )
    
    def _get_active_route_energy_at_arrival(self) -> Optional[int]:
        """Get raw estimated battery percentage at arrival.
        
        Returns:
            Estimated battery percentage at arrival, or None if no active route.
        """
        return self._get_nested(
            "drive_state", "active_route_energy_at_arrival", default=None
        )
    
    def get_active_route(self) -> str:
        """Get formatted active route information.
        
        Reports details about the currently active navigation route including
        destination, ETA, distance, and estimated battery at arrival.
        
        Returns:
            Human-readable active route information.
        """
        destination = self._get_active_route_destination()
        
        if destination is None:
            return "No active navigation route"
        
        minutes = self._get_active_route_minutes_to_arrival()
        miles = self._get_active_route_miles_to_arrival()
        energy = self._get_active_route_energy_at_arrival()
        
        parts = [f"Navigating to {destination}"]
        
        if miles is not None:
            parts.append(f"{miles:.1f} miles remaining")
        
        if minutes is not None:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            if hours > 0:
                parts.append(f"ETA in {hours}h {mins}m")
            else:
                parts.append(f"ETA in {mins}m")
        
        if energy is not None:
            parts.append(f"{energy}% battery at arrival")
        
        return ", ".join(parts)
    
    # =========================================================================
    # VEHICLE STATE & SECURITY
    # =========================================================================
    
    def _get_sentry_mode(self) -> bool:
        """Get raw Sentry Mode status.
        
        Returns:
            True if Sentry Mode is active, False otherwise.
        """
        return self._get_nested("vehicle_state", "sentry_mode", default=False)
    
    def _get_sentry_mode_available(self) -> bool:
        """Get raw Sentry Mode availability.
        
        Returns:
            True if Sentry Mode can be enabled, False otherwise.
        """
        return self._get_nested("vehicle_state", "sentry_mode_available", default=False)
    
    def get_sentry_mode(self) -> str:
        """Get formatted Sentry Mode status.
        
        Reports whether Tesla's Sentry Mode security feature is active. Sentry Mode
        uses cameras to monitor the vehicle's surroundings when parked.
        
        Returns:
            Human-readable Sentry Mode status.
        """
        is_on = self._get_sentry_mode()
        available = self._get_sentry_mode_available()
        
        if is_on:
            return "Sentry Mode is active (cameras monitoring surroundings)"
        elif available:
            return "Sentry Mode is off but available"
        else:
            return "Sentry Mode is unavailable"
    
    def _get_display_name(self) -> str:
        """Get raw vehicle display name.
        
        Returns:
            Vehicle's custom display name.
        """
        return self._get_nested("display_name", default="Unknown Vehicle")
    
    def get_display_name(self) -> str:
        """Get formatted vehicle display name.
        
        Reports the custom name assigned to the vehicle by its owner.
        
        Returns:
            Human-readable vehicle name.
        """
        name = self._get_display_name()
        return f"Vehicle name: {name}"
    
    # =========================================================================
    # SUMMARY METHODS
    # =========================================================================
    
    def get_all_heater_status(self) -> str:
        """Get formatted status of all heaters.
        
        Provides a comprehensive summary of all heating elements in the vehicle
        including seats, steering wheel, mirrors, and wipers.
        
        Returns:
            Human-readable summary of all heater statuses.
        """
        statuses = []
        
        # Seat heaters
        for seat, method in [
            ("Driver", self._get_seat_heater_left),
            ("Passenger", self._get_seat_heater_right),
            ("Rear left", self._get_seat_heater_rear_left),
            ("Rear center", self._get_seat_heater_rear_center),
            ("Rear right", self._get_seat_heater_rear_right),
        ]:
            level = method()
            if level > 0:
                statuses.append(f"{seat}: {self._heater_level_str(level)}")
        
        # Other heaters
        if self._get_steering_wheel_heater():
            level = self._get_steering_wheel_heat_level()
            statuses.append(f"Steering wheel: {self._heater_level_str(level)}")
        
        if self._get_side_mirror_heaters():
            statuses.append("Mirrors: on")
        
        if self._get_wiper_blade_heater():
            statuses.append("Wipers: on")
        
        if not statuses:
            return "All heaters are off"
        
        return "Active heaters: " + ", ".join(statuses)
    
    def get_battery_summary(self) -> str:
        """Get formatted battery and charging summary.
        
        Provides a comprehensive summary of battery state including level,
        energy remaining, charging status, and time to full charge.
        
        Returns:
            Human-readable battery and charging summary.
        """
        level = self._get_battery_level()
        energy = self._get_energy_remaining()
        state = self._get_charging_state()
        minutes = self._get_minutes_to_full_charge()
        limit = self._get_charge_limit_soc()
        
        parts = [f"Battery at {level}% ({energy:.1f} kWh)"]
        
        if state == "Charging":
            hours = minutes // 60
            mins = minutes % 60
            if hours > 0:
                parts.append(f"charging, {hours}h {mins}m to {limit}%")
            else:
                parts.append(f"charging, {mins}m to {limit}%")
        elif state == "Complete":
            parts.append("fully charged")
        else:
            parts.append(state.lower())
        
        return ", ".join(parts)

