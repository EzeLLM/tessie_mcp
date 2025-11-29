"""Tessie API client for fetching Tesla vehicle data and sending commands.

This module provides a robust client for interacting with the Tessie API,
including retry logic, comprehensive error handling, and logging for debugging.
"""

import os
import time
import requests
from typing import Optional, Dict, Any

from .constants import (
    TESSIE_BASE_URL,
    DEFAULT_API_TIMEOUT,
    MAX_API_RETRIES,
    RETRY_BACKOFF_FACTOR,
    HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_RATE_LIMITED,
    ENDPOINT_VEHICLES,
    ENDPOINT_BATTERY,
    ENDPOINT_BATTERY_HEALTH,
    ENDPOINT_LOCATION,
    ENDPOINT_TIRE_PRESSURE,
    ENDPOINT_STATUS,
    ENDPOINT_COMMAND_HONK,
    ENDPOINT_COMMAND_FLASH,
)
from .exceptions import (
    VehicleNotFoundError,
    TessieAPIError,
    AuthenticationError,
)
from .utils import setup_logging, sanitize_vin_for_logging, validate_vin


class TessieClient:
    """Client for interacting with the Tessie API.

    Handles authentication, retrieval of vehicle data, and command execution
    via the Tessie API with automatic retries and comprehensive error handling.

    Attributes:
        token: Tessie API access token
        base_url: Base URL for Tessie API
        timeout: Request timeout in seconds
        logger: Logger instance for debugging

    Example:
        >>> client = TessieClient()
        >>> battery_data = client.get_battery("5YJ3E1EA1KF123456")
        >>> print(battery_data['battery_level'])
        89.828
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = TESSIE_BASE_URL,
        timeout: int = DEFAULT_API_TIMEOUT
    ):
        """Initialize the Tessie API client.

        Args:
            token: Tessie API access token. If not provided, reads from
                   TESSIE_TOKEN environment variable.
            base_url: Base URL for Tessie API (default: https://api.tessie.com)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            AuthenticationError: If no token is provided and TESSIE_TOKEN env var is not set.
        """
        self.token = token or os.getenv("TESSIE_TOKEN")
        if not self.token:
            raise AuthenticationError(
                "Tessie API token required. Set TESSIE_TOKEN environment variable "
                "or pass token to constructor."
            )

        self.base_url = base_url
        self.timeout = timeout
        self.logger = setup_logging(__name__)

        self.logger.info("TessieClient initialized with base_url=%s", base_url)

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests.

        Returns:
            Dictionary containing Bearer token authorization header.
        """
        return {"Authorization": f"Bearer {self.token}"}

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            params: Optional query parameters
            retry_count: Current retry attempt (used internally)

        Returns:
            Parsed JSON response from the API

        Raises:
            TessieAPIError: If the API returns an error response
            AuthenticationError: If authentication fails
        """
        try:
            self.logger.debug(
                "Making %s request to %s (attempt %d/%d)",
                method,
                url,
                retry_count + 1,
                MAX_API_RETRIES + 1
            )

            if method == "GET":
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log response status
            self.logger.debug("Response status: %d", response.status_code)

            # Handle authentication errors
            if response.status_code in [HTTP_UNAUTHORIZED, HTTP_FORBIDDEN]:
                raise AuthenticationError(
                    f"Authentication failed (HTTP {response.status_code}). "
                    "Please check your TESSIE_TOKEN."
                )

            # Handle rate limiting with retry
            if response.status_code == HTTP_RATE_LIMITED:
                if retry_count < MAX_API_RETRIES:
                    wait_time = RETRY_BACKOFF_FACTOR ** retry_count
                    self.logger.warning(
                        "Rate limited. Waiting %ds before retry...",
                        wait_time
                    )
                    time.sleep(wait_time)
                    return self._make_request(method, url, params, retry_count + 1)
                else:
                    raise TessieAPIError(
                        "Rate limit exceeded. Please try again later.",
                        status_code=response.status_code
                    )

            # Raise for other HTTP errors
            response.raise_for_status()

            # Parse and return JSON response
            data = response.json()
            self.logger.debug("Request successful, received %d bytes", len(response.content))
            return data

        except requests.exceptions.Timeout:
            if retry_count < MAX_API_RETRIES:
                wait_time = RETRY_BACKOFF_FACTOR ** retry_count
                self.logger.warning(
                    "Request timeout. Waiting %ds before retry...",
                    wait_time
                )
                time.sleep(wait_time)
                return self._make_request(method, url, params, retry_count + 1)
            else:
                raise TessieAPIError(f"Request timeout after {MAX_API_RETRIES} retries")

        except requests.exceptions.RequestException as e:
            raise TessieAPIError(f"Request failed: {str(e)}")

    # =========================================================================
    # VEHICLE DISCOVERY
    # =========================================================================

    def fetch_vehicles(self) -> list[dict]:
        """Fetch all vehicles from the Tessie API.

        Returns:
            List of vehicle data dictionaries.

        Raises:
            TessieAPIError: If the API request fails.
            AuthenticationError: If authentication fails.

        Example:
            >>> vehicles = client.fetch_vehicles()
            >>> for vehicle in vehicles:
            ...     print(vehicle['vin'], vehicle['display_name'])
        """
        self.logger.info("Fetching all vehicles")
        url = f"{self.base_url}{ENDPOINT_VEHICLES}"
        params = {"access_token": self.token}

        data = self._make_request("GET", url, params=params)
        vehicles = data.get("results", [])

        self.logger.info("Found %d vehicle(s)", len(vehicles))
        return vehicles

    def get_vehicle_by_vin(self, vin: str) -> Optional[dict]:
        """Get vehicle data by VIN.

        Args:
            vin: The VIN to search for (17-character alphanumeric string)

        Returns:
            Vehicle data dictionary if found, None otherwise.

        Raises:
            TessieAPIError: If the API request fails.
            ValueError: If VIN format appears invalid.

        Example:
            >>> vehicle = client.get_vehicle_by_vin("5YJ3E1EA1KF123456")
            >>> if vehicle:
            ...     print(vehicle['display_name'])
        """
        if not validate_vin(vin):
            self.logger.warning("VIN '%s' appears to have invalid format", vin)

        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Searching for vehicle with VIN %s", sanitized_vin)

        vehicles = self.fetch_vehicles()

        for vehicle in vehicles:
            if vehicle.get("vin") == vin:
                self.logger.info("Found vehicle: %s", vehicle.get("display_name"))
                return vehicle

        self.logger.warning("Vehicle with VIN %s not found", sanitized_vin)
        return None

    # =========================================================================
    # TELEMETRY ENDPOINTS
    # =========================================================================

    def get_battery(self, vin: str) -> Dict[str, Any]:
        """Get battery information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Battery data including level, range, energy, voltage, current, temp.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> data = client.get_battery("5YJ3E1EA1KF123456")
            >>> print(f"Battery: {data['battery_level']}%")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching battery data for VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_BATTERY.format(vin=vin)}"
        return self._make_request("GET", url)

    def get_battery_health(self, vin: str) -> Dict[str, Any]:
        """Get battery health information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Battery health data including max range and capacity.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> data = client.get_battery_health("5YJ3E1EA1KF123456")
            >>> print(f"Capacity: {data['result']['capacity']} kWh")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching battery health for VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_BATTERY_HEALTH.format(vin=vin)}"
        return self._make_request("GET", url)

    def get_location(self, vin: str) -> Dict[str, Any]:
        """Get location information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Location data including lat, lon, address, saved location.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> data = client.get_location("5YJ3E1EA1KF123456")
            >>> print(f"Address: {data['address']}")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching location for VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_LOCATION.format(vin=vin)}"
        return self._make_request("GET", url)

    def get_tire_pressure(self, vin: str) -> Dict[str, Any]:
        """Get tire pressure information for a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Tire pressure data for all four tires with status.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> data = client.get_tire_pressure("5YJ3E1EA1KF123456")
            >>> print(f"Front left: {data['front_left']} bar")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching tire pressure for VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_TIRE_PRESSURE.format(vin=vin)}"
        return self._make_request("GET", url)

    def get_status(self, vin: str) -> Dict[str, Any]:
        """Get status of a vehicle.

        Args:
            vin: Vehicle VIN.

        Returns:
            Status data (asleep, waiting_for_sleep, or awake).

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> data = client.get_status("5YJ3E1EA1KF123456")
            >>> print(f"Status: {data['status']}")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching status for VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_STATUS.format(vin=vin)}"
        return self._make_request("GET", url)

    # =========================================================================
    # LEGACY ENDPOINT (for backwards compatibility during migration)
    # =========================================================================

    def get_vehicle_state(self, vin: str) -> Optional[Dict[str, Any]]:
        """Get the last known state of a vehicle by VIN.

        This is a legacy method that fetches the full vehicle state in one call.
        New code should use the specific endpoint methods (get_battery,
        get_location, etc.) for better performance.

        Args:
            vin: The VIN to search for.

        Returns:
            Vehicle's last_state dictionary if found, None otherwise.

        Raises:
            VehicleNotFoundError: If vehicle with VIN is not found.
            TessieAPIError: If the API request fails.
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Fetching full vehicle state for VIN %s", sanitized_vin)

        vehicle = self.get_vehicle_by_vin(vin)

        if vehicle is None:
            raise VehicleNotFoundError(vin)

        return vehicle.get("last_state")

    # =========================================================================
    # CONTROL COMMANDS
    # =========================================================================

    def honk_horn(self, vin: str) -> Dict[str, Any]:
        """Honk the vehicle horn.

        Args:
            vin: Vehicle VIN.

        Returns:
            Command response from Tessie API.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> response = client.honk_horn("5YJ3E1EA1KF123456")
            >>> if response.get("result"):
            ...     print("Horn honked successfully!")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Sending honk command to VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_COMMAND_HONK.format(vin=vin)}"
        params = {"access_token": self.token}

        return self._make_request("POST", url, params=params)

    def flash_lights(self, vin: str) -> Dict[str, Any]:
        """Flash the vehicle lights.

        Args:
            vin: Vehicle VIN.

        Returns:
            Command response from Tessie API.

        Raises:
            TessieAPIError: If the API request fails.

        Example:
            >>> response = client.flash_lights("5YJ3E1EA1KF123456")
            >>> if response.get("result"):
            ...     print("Lights flashed successfully!")
        """
        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Sending flash lights command to VIN %s", sanitized_vin)

        url = f"{self.base_url}{ENDPOINT_COMMAND_FLASH.format(vin=vin)}"
        return self._make_request("POST", url)
