"""Control tool definitions and dispatch helpers."""

from typing import Callable

from mcp.types import Tool

from .service import Control


CONTROL_TOOL_SPECS: list[tuple[str, str]] = [
    ("lock_doors", "Lock the vehicle doors"),
    ("unlock_doors", "Unlock the vehicle doors"),
    ("honk_horn", "Honk the vehicle horn"),
    ("flash_lights", "Flash the vehicle lights"),
    ("start_climate", "Start climate/preconditioning"),
    ("stop_climate", "Stop climate/preconditioning"),
    ("set_temperature", "Set cabin temperature in Celsius (optionally wait for completion)"),
]

CONTROL_TOOLS: list[Tool] = [
    Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": {
                "temperature": {"type": "number", "description": "Target cabin temperature in Celsius"},
                "wait_for_completion": {"type": "boolean", "description": "Wait for command to finish before returning"},
            },
            "required": ["temperature"] if name == "set_temperature" else [],
        },
    )
    for name, description in CONTROL_TOOL_SPECS
]


def build_control_dispatch(control: Control) -> dict[str, Callable[[dict], str]]:
    """Build a mapping of control tool names to bound methods."""
    dispatch: dict[str, Callable[[dict], str]] = {}

    for name, _ in CONTROL_TOOL_SPECS:
        method = getattr(control, name, None)
        if method is None:
            raise AttributeError(f"Control missing expected method {name}")

        if name == "set_temperature":
            dispatch[name] = lambda args, method=method: method(
                temperature=args.get("temperature"),
                wait_for_completion=args.get("wait_for_completion"),
            )
        else:
            dispatch[name] = lambda _args=None, method=method: method()

    return dispatch


__all__ = ["CONTROL_TOOLS", "CONTROL_TOOL_SPECS", "build_control_dispatch"]
