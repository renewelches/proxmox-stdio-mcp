"""Human-friendly formatting utilities for Proxmox API responses."""

from typing import Any

BYTE_FIELDS = {
    "maxmem",
    "maxdisk",
    "mem",
    "disk",
    "balloon_min",
    "memory",
    "rootfs",
    "swap",
    "maxswap",
    "freemem",
}

UPTIME_FIELDS = {"uptime"}


def format_bytes(value: int | float) -> str:
    """Convert bytes to a human-readable string (KB, MB, GB, TB)."""
    if not isinstance(value, (int, float)):
        return str(value)

    abs_val = abs(value)
    if abs_val >= 1 << 40:
        return f"{value / (1 << 40):.2f} TB"
    if abs_val >= 1 << 30:
        return f"{value / (1 << 30):.2f} GB"
    if abs_val >= 1 << 20:
        return f"{value / (1 << 20):.2f} MB"
    if abs_val >= 1 << 10:
        return f"{value / (1 << 10):.2f} KB"
    return f"{value} B"


def format_uptime(seconds: int | float) -> str:
    """Convert seconds to a human-readable uptime string."""
    if not isinstance(seconds, (int, float)):
        return str(seconds)

    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def format_response(data: dict | list) -> dict | list:
    """Recursively format known fields in a Proxmox API response."""
    if isinstance(data, list):
        return [format_response(item) for item in data]
    if not isinstance(data, dict):
        return data

    result: dict[Any, Any] = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            result[key] = format_response(value)
        elif key in BYTE_FIELDS and isinstance(value, (int, float)):
            result[key] = format_bytes(value)
        elif key in UPTIME_FIELDS and isinstance(value, (int, float)):
            result[key] = format_uptime(value)
        else:
            result[key] = value
    return result
