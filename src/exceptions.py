"""Custom exceptions for the Tessie MCP server.

This module defines domain-specific exceptions that provide better error
messages and debugging information than generic Python exceptions.
"""


class TessieMCPError(Exception):
    """Base exception for all Tessie MCP errors.

    All custom exceptions in this module inherit from this base class,
    making it easy to catch all Tessie MCP-related errors.
    """
    pass


class VehicleNotFoundError(TessieMCPError):
    """Raised when a vehicle with the specified VIN cannot be found.

    This typically occurs when:
    - The VIN is incorrect or malformed
    - The vehicle is not associated with the Tessie account
    - The Tessie API token doesn't have access to the vehicle

    Args:
        vin: The VIN that was not found
        message: Optional custom error message

    Example:
        >>> raise VehicleNotFoundError("5YJ3E1EA1KF123456")
        VehicleNotFoundError: Vehicle with VIN '5YJ3E1EA1KF123456' not found
    """

    def __init__(self, vin: str, message: str = None):
        self.vin = vin
        if message is None:
            message = f"Vehicle with VIN '{vin}' not found. Please verify the VIN is correct."
        super().__init__(message)


class TessieAPIError(TessieMCPError):
    """Raised when the Tessie API returns an error response.

    This exception captures both HTTP errors and API-level errors returned
    by Tessie's endpoints.

    Args:
        message: Error message describing the API failure
        status_code: HTTP status code if available
        response_data: Raw response data from the API

    Example:
        >>> raise TessieAPIError("Rate limit exceeded", status_code=429)
    """

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.status_code = status_code
        self.response_data = response_data

        if status_code:
            message = f"Tessie API error (HTTP {status_code}): {message}"
        else:
            message = f"Tessie API error: {message}"

        super().__init__(message)


class AuthenticationError(TessieMCPError):
    """Raised when authentication with the Tessie API fails.

    This typically occurs when:
    - The TESSIE_TOKEN is missing or invalid
    - The token has expired
    - The token doesn't have required permissions

    Example:
        >>> raise AuthenticationError("Invalid or expired token")
    """
    pass


class ConfigurationError(TessieMCPError):
    """Raised when there's a configuration problem.

    This typically occurs when:
    - Required environment variables are missing
    - Configuration values are invalid
    - Config file is malformed

    Example:
        >>> raise ConfigurationError("VEHICLE_VIN not set in environment")
    """
    pass


class VehicleCommandError(TessieMCPError):
    """Raised when a vehicle command fails to execute.

    This exception is used for control commands (honk, flash, lock, etc.)
    that fail to execute on the vehicle.

    Args:
        command: The command that failed (e.g., "honk_horn")
        reason: Reason for failure from the API
        vin: The VIN of the vehicle

    Example:
        >>> raise VehicleCommandError("honk_horn", "Vehicle is asleep")
    """

    def __init__(self, command: str, reason: str = None, vin: str = None):
        self.command = command
        self.reason = reason
        self.vin = vin

        message = f"Failed to execute command '{command}'"
        if reason:
            message += f": {reason}"
        if vin:
            message += f" (VIN: {vin})"

        super().__init__(message)


class DataValidationError(TessieMCPError):
    """Raised when data validation fails.

    This exception is used when API responses don't match expected formats
    or when required fields are missing.

    Example:
        >>> raise DataValidationError("Battery data missing 'battery_level' field")
    """
    pass
