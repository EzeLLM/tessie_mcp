"""Tesla vehicle control interface (stubbed for upcoming implementation)."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from ..tessie_client import TessieClient

# Load .env from project root for standalone usage
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Control:
    """Control entry point for issuing Tessie actions.

    Provides methods to control the vehicle including honking, flashing lights,
    locking/unlocking doors, and climate control.
    """

    def __init__(self, vin: str, client: Optional[TessieClient] = None):
        self.vin = vin
        self.client = client or TessieClient()
    
    def _coming_soon(self, action: str) -> str:
        """Friendly placeholder until control wiring is live."""
        return (
            f"Control action '{action}' is not enabled yet. "
            "Control endpoints will ship later this week."
        )

    def lock_doors(self) -> str:
        return self._coming_soon("lock_doors")

    def unlock_doors(self) -> str:
        return self._coming_soon("unlock_doors")

    def honk_horn(self) -> str:
        """Honk the vehicle horn.

        Returns:
            Success or error message from the API.
        """
        try:
            response = self.client.honk_horn(self.vin)
            result = response.get("result", False)

            if result:
                return "Successfully honked the horn!"
            else:
                error = response.get("reason", "Unknown error")
                return f"Failed to honk horn: {error}"

        except Exception as e:
            return f"Error honking horn: {str(e)}"

    def flash_lights(self) -> str:
        """Flash the vehicle lights.

        Returns:
            Success or error message from the API.
        """
        try:
            response = self.client.flash_lights(self.vin)
            result = response.get("result", False)

            if result:
                return "Successfully flashed the lights!"
            else:
                error = response.get("reason", "Unknown error")
                return f"Failed to flash lights: {error}"

        except Exception as e:
            return f"Error flashing lights: {str(e)}"

    def start_climate(self) -> str:
        return self._coming_soon("start_climate")

    def stop_climate(self) -> str:
        return self._coming_soon("stop_climate")
