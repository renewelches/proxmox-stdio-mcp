import os
import logging

from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)


def create_proxmox_client() -> ProxmoxAPI:
    """Create a Proxmox API client using environment variables.

    Authentication priority:
    1. Username + Password (if both PROXMOX_USER and PROXMOX_PASSWORD are set)
    2. API Token (if both PROXMOX_TOKEN_ID and PROXMOX_TOKEN_SECRET are set)

    Required environment variables:
    - PROXMOX_HOST: Proxmox host (e.g. "pve.example.com" or "192.168.1.100")

    Optional:
    - PROXMOX_PORT: Port number (default: 8006)
    - PROXMOX_VERIFY_SSL: SSL verification, "true" or "false" (default: "true")
    """
    host = os.environ.get("PROXMOX_HOST")
    if not host:
        raise ValueError("PROXMOX_HOST environment variable is required")

    # Strip protocol prefix if provided — proxmoxer expects just the hostname
    for prefix in ("https://", "http://"):
        if host.startswith(prefix):
            host = host[len(prefix) :]
    # Strip trailing port if embedded in the host
    if ":" in host:
        host, _, port_str = host.partition(":")
        os.environ.setdefault("PROXMOX_PORT", port_str.rstrip("/"))

    port = int(os.environ.get("PROXMOX_PORT", "8006"))
    verify_ssl = os.environ.get("PROXMOX_VERIFY_SSL", "true").lower() == "true"

    user = os.environ.get("PROXMOX_USER")
    password = os.environ.get("PROXMOX_PASSWORD")
    token_id = os.environ.get("PROXMOX_TOKEN_ID")
    token_secret = os.environ.get("PROXMOX_TOKEN_SECRET")

    # Password auth takes precedence
    if user and password:
        logger.info("Authenticating with username/password for user: %s", user)
        return ProxmoxAPI(
            host,
            port=port,
            user=user,
            password=password,
            verify_ssl=verify_ssl,
            backend="https",
        )

    if token_id and token_secret:
        # token_id format: "user@realm!token-name"
        # proxmoxer expects user and token_name separately
        if "!" in token_id:
            user_part, token_name = token_id.split("!", 1)
        else:
            raise ValueError(
                "PROXMOX_TOKEN_ID must be in format 'user@realm!token-name'"
            )
        logger.info("Authenticating with API token for user: %s", user_part)
        return ProxmoxAPI(
            host,
            port=port,
            user=user_part,
            token_name=token_name,
            token_value=token_secret,
            verify_ssl=verify_ssl,
            backend="https",
        )

    raise ValueError(
        "Authentication not configured. Set either "
        "PROXMOX_USER + PROXMOX_PASSWORD or "
        "PROXMOX_TOKEN_ID + PROXMOX_TOKEN_SECRET environment variables."
    )
