"""LXC container-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all LXC resources with the MCP server."""

    @mcp.tool()
    def get_node_lxcs(node: str) -> str:
        """Get all LXC containers on a specific node.

        Args:
            node: The node name (e.g. "pve1")

        Returns a list of LXC containers with their status, CPU/memory usage, etc.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        lxcs = proxmox.nodes(node).lxc.get()
        return json.dumps(format_response(lxcs), indent=2)

    @mcp.tool()
    def get_all_lxcs() -> str:
        """Get all LXC containers from all nodes in the cluster.

        Returns LXC containers grouped by node name.
        Permission required: VM.Audit on /vms/{vmid}, Sys.Audit on /
        """
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        result = {}
        for node_info in nodes:
            node_name = node_info["node"]
            lxcs = proxmox.nodes(node_name).lxc.get()
            result[node_name] = format_response(lxcs)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_lxc_status(node: str, vmid: int) -> str:
        """Get the current status of an LXC container.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns detailed status including CPU, memory, network, and disk usage.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).lxc(vmid).status.current.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    def get_lxc_config(node: str, vmid: int) -> str:
        """Get the configuration of an LXC container.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns the full configuration including CPU, memory, storage, and network settings.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        config = proxmox.nodes(node).lxc(vmid).config.get()
        return json.dumps(format_response(config), indent=2)
