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

    def lock_doors(self) -> str:
        """Lock the vehicle doors.

        Returns:
            Status message (currently a placeholder)

        Note:
            This command is not yet implemented. It will be wired to the
            Tessie API in a future update.
        """
        return self._coming_soon("lock_doors")

    def unlock_doors(self) -> str:
        """Unlock the vehicle doors.

        Returns:
            Status message (currently a placeholder)

        Note:
            This command is not yet implemented. It will be wired to the
            Tessie API in a future update.
        """
        return self._coming_soon("unlock_doors")

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
        sanitized_vin = sanitize_vin_for_logging(self.vin)
        self.logger.info("Executing honk_horn for VIN %s", sanitized_vin)

        try:
            response = self.client.honk_horn(self.vin)
            result = response.get("result", False)

            if result:
                self.logger.info("Horn honked successfully for VIN %s", sanitized_vin)
                return "Successfully honked the horn!"
            else:
                error = response.get("reason", "Unknown error")
                self.logger.warning(
                    "Honk failed for VIN %s: %s",
                    sanitized_vin,
                    error
                )
                raise VehicleCommandError("honk_horn", error, self.vin)

        except VehicleCommandError:
            # Re-raise our custom exception
            raise
        except TessieAPIError as e:
            self.logger.error(
                "API error honking horn for VIN %s: %s",
                sanitized_vin,
                str(e)
            )
            return f"Failed to honk horn: {str(e)}"
        except Exception as e:
            self.logger.error(
                "Unexpected error honking horn for VIN %s: %s",
                sanitized_vin,
                str(e),
                exc_info=True
            )
            return f"Error honking horn: {str(e)}"

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
        sanitized_vin = sanitize_vin_for_logging(self.vin)
        self.logger.info("Executing flash_lights for VIN %s", sanitized_vin)

        try:
            response = self.client.flash_lights(self.vin)
            result = response.get("result", False)

            if result:
                self.logger.info("Lights flashed successfully for VIN %s", sanitized_vin)
                return "Successfully flashed the lights!"
            else:
                error = response.get("reason", "Unknown error")
                self.logger.warning(
                    "Flash failed for VIN %s: %s",
                    sanitized_vin,
                    error
                )
                raise VehicleCommandError("flash_lights", error, self.vin)

        except VehicleCommandError:
            # Re-raise our custom exception
            raise
        except TessieAPIError as e:
            self.logger.error(
                "API error flashing lights for VIN %s: %s",
                sanitized_vin,
                str(e)
            )
            return f"Failed to flash lights: {str(e)}"
        except Exception as e:
            self.logger.error(
                "Unexpected error flashing lights for VIN %s: %s",
                sanitized_vin,
                str(e),
                exc_info=True
            )
            return f"Error flashing lights: {str(e)}"

    def start_climate(self) -> str:
        """Start climate control preconditioning.

        Returns:
            Status message (currently a placeholder)

        Note:
            This command is not yet implemented. It will be wired to the
            Tessie API in a future update.
        """
        return self._coming_soon("start_climate")

    def stop_climate(self) -> str:
        """Stop climate control preconditioning.

        Returns:
            Status message (currently a placeholder)

        Note:
            This command is not yet implemented. It will be wired to the
            Tessie API in a future update.
        """
        return self._coming_soon("stop_climate")
