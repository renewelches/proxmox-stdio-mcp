"""Cluster-level MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register cluster resources with the MCP server."""

    @mcp.tool()
    @mcp.resource("proxmox://cluster/status")
    @handle_proxmox_error('["perm", "/", ["Sys.Audit"]]')
    def get_cluster_status() -> str:
        """Cluster health, quorum status, and summary of all nodes and their states."""
        proxmox = create_proxmox_client()
        status = proxmox.cluster.status.get()
        return json.dumps(format_response(status), indent=2)
