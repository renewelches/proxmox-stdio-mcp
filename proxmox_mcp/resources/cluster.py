"""Cluster-level MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register cluster resources with the MCP server."""

    @mcp.tool()
    def get_cluster_status() -> str:
        """Get the overall cluster status.

        Returns cluster health, quorum status, and a summary of all nodes and their states.
        Useful for getting a quick overview of the entire Proxmox environment.
        Permission required: Sys.Audit on /
        """
        proxmox = create_proxmox_client()
        status = proxmox.cluster.status.get()
        return json.dumps(format_response(status), indent=2)
