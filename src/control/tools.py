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
]

CONTROL_TOOLS: list[Tool] = [
    Tool(
        name=name,
        description=description,
        inputSchema={"type": "object", "properties": {}, "required": []},
    )
    for name, description in CONTROL_TOOL_SPECS
]


def build_control_dispatch(control: Control) -> dict[str, Callable[[], str]]:
    """Build a mapping of control tool names to bound methods."""
    dispatch: dict[str, Callable[[], str]] = {}
    for name, _ in CONTROL_TOOL_SPECS:
        method = getattr(control, name, None)
        if method is None:
            raise AttributeError(f"Control missing expected method {name}")
        dispatch[name] = method
    return dispatch


__all__ = ["CONTROL_TOOLS", "CONTROL_TOOL_SPECS", "build_control_dispatch"]
