"""Tesla vehicle control interface via Tessie API.

This module provides methods to control the vehicle including honking, flashing
lights, locking/unlocking doors, and climate control.
"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from ..tessie_client import TessieClient
from ..exceptions import VehicleCommandError, TessieAPIError
from ..utils import setup_logging, sanitize_vin_for_logging

# Load .env from project root for standalone usage
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Control:
    """Control entry point for issuing Tessie actions.

    Provides methods to control the vehicle including honking, flashing lights,
    locking/unlocking doors, and climate control.

    Attributes:
        vin: Vehicle Identification Number
        client: TessieClient instance for API calls
        logger: Logger instance for debugging

    Example:
        >>> control = Control(vin="5YJ3E1EA1KF123456")
        >>> result = control.honk_horn()
        >>> print(result)
        Successfully honked the horn!
    """

    def __init__(self, vin: str, client: Optional[TessieClient] = None):
        """Initialize the Control service.

        Args:
            vin: Vehicle VIN to control
            client: Optional TessieClient instance (creates one if not provided)
        """
        self.vin = vin
        self.client = client or TessieClient()
        self.logger = setup_logging(__name__)

        sanitized_vin = sanitize_vin_for_logging(vin)
        self.logger.info("Control service initialized for VIN %s", sanitized_vin)

    def _coming_soon(self, action: str) -> str:
        """Friendly placeholder for commands not yet implemented.

        Args:
            action: Name of the action/command

        Returns:
            Message indicating the command is not yet available
        """
        self.logger.debug("Placeholder called for action: %s", action)
        return (
            f"Control action '{action}' is not enabled yet. "
            "Control endpoints will ship soon."
        )

    def _run_command(self, action: str, api_call, success_message: str) -> str:
        """Execute a control command with consistent logging and errors."""
        sanitized_vin = sanitize_vin_for_logging(self.vin)
        self.logger.info("Executing %s for VIN %s", action, sanitized_vin)

        try:
            response = api_call()
            result = response.get("result", False)

            if result:
                self.logger.info("%s succeeded for VIN %s", action, sanitized_vin)
                return success_message
            else:
                error = response.get("reason", "Unknown error")
                self.logger.warning("%s failed for VIN %s: %s", action, sanitized_vin, error)
                raise VehicleCommandError(action, error, self.vin)

        except VehicleCommandError:
            raise
        except TessieAPIError as e:
            self.logger.error("API error during %s for VIN %s: %s", action, sanitized_vin, str(e))
            return f"Failed to {action.replace('_', ' ')}: {str(e)}"
        except Exception as e:
            self.logger.error(
                "Unexpected error during %s for VIN %s: %s",
                action,
                sanitized_vin,
                str(e),
                exc_info=True
            )
            return f"Error attempting to {action.replace('_', ' ')}: {str(e)}"

    def lock_doors(self) -> str:
        """Lock the vehicle doors."""
        return self._run_command(
            "lock_doors",
            lambda: self.client.lock_doors(self.vin),
            "Vehicle locked."
        )

    def unlock_doors(self) -> str:
        """Unlock the vehicle doors.

        Returns:
            Status message from the API
        """
        return self._run_command(
            "unlock_doors",
            lambda: self.client.unlock_doors(self.vin),
            "Vehicle unlocked."
        )

    def honk_horn(self) -> str:
        """Honk the vehicle horn.

        This command will cause the vehicle horn to honk once. The vehicle
        must be awake for this command to work.

        Returns:
            Success or error message from the API

        Example:
            >>> control = Control(vin="5YJ3E1EA1KF123456")
            >>> print(control.honk_horn())
            Successfully honked the horn!
        """
        return self._run_command(
            "honk_horn",
            lambda: self.client.honk_horn(self.vin),
            "Successfully honked the horn!"
        )

    def flash_lights(self) -> str:
        """Flash the vehicle lights.

        This command will cause the vehicle's exterior lights to flash briefly.
        Useful for locating the vehicle in a parking lot. The vehicle must be
        awake for this command to work.

        Returns:
            Success or error message from the API

        Example:
            >>> control = Control(vin="5YJ3E1EA1KF123456")
            >>> print(control.flash_lights())
            Successfully flashed the lights!
        """
        return self._run_command(
            "flash_lights",
            lambda: self.client.flash_lights(self.vin),
            "Successfully flashed the lights!"
        )

    def start_climate(self) -> str:
        """Start climate control preconditioning.

        Returns:
            Status message from the API
        """
        return self._run_command(
            "start_climate",
            lambda: self.client.start_climate(self.vin),
            "Climate/preconditioning started."
        )

    def stop_climate(self) -> str:
        """Stop climate control preconditioning.

        Returns:
            Status message from the API
        """
        return self._run_command(
            "stop_climate",
            lambda: self.client.stop_climate(self.vin),
            "Climate/preconditioning stopped."
        )

    def set_temperature(
        self,
        temperature: float | int | None,
        wait_for_completion: Optional[bool] = True
    ) -> str:
        """Set cabin temperature in Celsius."""
        if temperature is None:
            return "Temperature is required."

        try:
            temp_value = float(temperature)
        except (TypeError, ValueError):
            return "Temperature must be a number in Celsius."

        return self._run_command(
            "set_temperature",
            lambda: self.client.set_temperatures(
                self.vin,
                temperature=temp_value,
                wait_for_completion=wait_for_completion,
            ),
            f"Set cabin temperature to {temp_value:.1f} C."
        )
