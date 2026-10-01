"""Error handling for Proxmox API calls with permission-aware messages."""

import functools
import logging
from collections.abc import Callable
from typing import Any

import requests
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from proxmoxer.core import ResourceException

logger = logging.getLogger(__name__)


class ProxmoxError(ToolError, ResourceError):
    """An anticipated failure whose message should reach the client.

    MCPServer replaces any other exception with a generic "Error executing ..."
    message. Read functions are registered as both tools and resources, so this
    subclasses both error types to surface the message either way.
    """


def _format_permission_error(
    status_code: int,
    content: str,
    required_permission: str,
) -> str:
    """Format a Proxmox API error into a clear, actionable message."""
    if status_code == 403:
        return (
            f"Permission denied: {required_permission} — "
            f"ensure the API token/user has this privilege. "
            f"Proxmox response: {content}"
        )
    if status_code == 401:
        return (
            f"Authentication failed: check PROXMOX_TOKEN_ID/PROXMOX_TOKEN_SECRET "
            f"or PROXMOX_USER/PROXMOX_PASSWORD. Proxmox response: {content}"
        )
    if status_code == 404:
        return f"Resource not found: {content}"
    if status_code == 500:
        return f"Proxmox internal error: {content}"
    return f"Proxmox API error ({status_code}): {content}"


def handle_proxmox_error(required_permission: str) -> Callable:
    """Decorator that catches proxmoxer errors and returns clear messages.

    Args:
        required_permission: Human-readable permission requirement,
            e.g. '["perm", "/", ["Sys.Audit"]]'
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except ResourceException as exc:
                msg = _format_permission_error(exc.status_code, exc.content, required_permission)
                logger.error(msg)
                raise ProxmoxError(msg) from exc
            except ValueError as exc:
                raise ProxmoxError(str(exc)) from exc
            except requests.RequestException as exc:
                # Unreachable host, TLS verification failure, timeout.
                raise ProxmoxError(f"Cannot reach Proxmox: {exc}") from exc

        return wrapper

    return decorator
