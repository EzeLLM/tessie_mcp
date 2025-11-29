"""Tessie API client for fetching Tesla vehicle data and sending commands."""

import os
import requests
from typing import Optional


class TessieClient:
    """Client for interacting with the Tessie API.

    Handles authentication, retrieval of vehicle data, and command execution
    via the Tessie API.
    """

    BASE_URL = "https://api.tessie.com"

    def __init__(self, token: Optional[str] = None):
        """Initialize the Tessie API client.

        Args:
            token: Tessie API access token. If not provided, reads from
                   TESSIE_TOKEN environment variable.

        Raises:
            ValueError: If no token is provided and TESSIE_TOKEN env var is not set.
        """
        self.token = token or os.getenv("TESSIE_TOKEN")
        if not self.token:
            raise ValueError(
                "Tessie API token required. Set TESSIE_TOKEN environment variable "
                "or pass token to constructor."
            )

    def _get_headers(self) -> dict:
        """Get authorization headers for API requests.

        Returns:
            Dictionary containing Bearer token authorization header.
        """
        return {"Authorization": f"Bearer {self.token}"}

    # =========================================================================
    # VEHICLE DISCOVERY
    # =========================================================================

    def fetch_vehicles(self) -> list[dict]:
        """Fetch all vehicles from the Tessie API.

        Returns:
            List of vehicle data dictionaries.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/vehicles"
        params = {"access_token": self.token}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data.get("results", [])

    def get_vehicle_by_vin(self, vin: str) -> Optional[dict]:
        """Get vehicle data by VIN.

        Args:
            vin: The VIN to search for.

        Returns:
            Vehicle data dictionary if found, None otherwise.

        Raises:
            requests.RequestException: If the API request fails.
        """
        vehicles = self.fetch_vehicles()

        for vehicle in vehicles:
            if vehicle.get("vin") == vin:
                return vehicle

        return None

    # =========================================================================
    # TELEMETRY ENDPOINTS
    # =========================================================================

    def get_battery(self, vin: str) -> dict:
        """Get battery information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Battery data including level, range, energy, voltage, current, temp.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/battery"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_battery_health(self, vin: str) -> dict:
        """Get battery health information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Battery health data including max range and capacity.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/battery_health"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_location(self, vin: str) -> dict:
        """Get location information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Location data including lat, lon, address, saved location.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/location"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_tire_pressure(self, vin: str) -> dict:
        """Get tire pressure information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Tire pressure data for all four tires with status.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/tire_pressure"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def get_status(self, vin: str) -> dict:
        """Get status of a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Status data (asleep, waiting_for_sleep, or awake).

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/status"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # LEGACY ENDPOINT (for backwards compatibility during migration)
    # =========================================================================

    def get_vehicle_state(self, vin: str) -> Optional[dict]:
        """Get the last known state of a vehicle by VIN.

        This is a legacy method that fetches the full vehicle state in one call.
        New code should use the specific endpoint methods (get_battery,
        get_location, etc.) for better performance.

        Args:
            vin: The VIN to search for.

        Returns:
            Vehicle's last_state dictionary if found, None otherwise.

        Raises:
            requests.RequestException: If the API request fails.
        """
        vehicle = self.get_vehicle_by_vin(vin)

        if vehicle:
            return vehicle.get("last_state")

        return None

    # =========================================================================
    # CONTROL COMMANDS
    # =========================================================================

    def honk_horn(self, vin: str) -> dict:
        """Honk the vehicle horn.

        Args:
            vin: Vehicle VIN.

        Returns:
            Command response from Tessie API.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/command/honk"
        params = {"access_token": self.token}
        response = requests.post(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def flash_lights(self, vin: str) -> dict:
        """Flash the vehicle lights.

        Args:
            vin: Vehicle VIN.

        Returns:
            Command response from Tessie API.

        Raises:
            requests.RequestException: If the API request fails.
        """
        url = f"{self.BASE_URL}/{vin}/command/flash"
        response = requests.post(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()
