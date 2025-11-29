"""Tessie API client for fetching Tesla vehicle data."""

import os
import requests
from typing import Optional


class TessieClient:
    """Client for interacting with the Tessie API.
    
    Handles authentication and retrieval of vehicle data from the Tessie API.
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
    
    def get_vehicle_by_plate(self, plate: str) -> Optional[dict]:
        """Get vehicle data by license plate.
        
        Args:
            plate: The license plate to search for.
        
        Returns:
            Vehicle data dictionary if found, None otherwise.
        
        Raises:
            requests.RequestException: If the API request fails.
        """
        vehicles = self.fetch_vehicles()
        
        for vehicle in vehicles:
            if vehicle.get("plate") == plate:
                return vehicle
        
        return None
    
    def get_vehicle_state(self, plate: str) -> Optional[dict]:
        """Get the last known state of a vehicle by plate.
        
        Args:
            plate: The license plate to search for.
        
        Returns:
            Vehicle's last_state dictionary if found, None otherwise.
        
        Raises:
            requests.RequestException: If the API request fails.
        """
        vehicle = self.get_vehicle_by_plate(plate)
        
        if vehicle:
            return vehicle.get("last_state")
        
        return None

