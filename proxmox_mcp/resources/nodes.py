"""Node-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all node resources with the MCP server."""

    @mcp.tool()
    def get_nodes() -> str:
        """Get all nodes in the Proxmox cluster.

        Returns a list of nodes with their status, CPU/memory usage, and uptime.
        Permission required: Sys.Audit on /
        """
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        return json.dumps(format_response(nodes), indent=2)

    @mcp.tool()
    def get_node_status(node: str) -> str:
        """Get detailed status of a specific node.

        Args:
            node: The node name (e.g. "pve1")

        Returns CPU, memory, swap, filesystem, kernel version, and load averages.
        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).status.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    def get_node_hosts(node: str) -> str:
        """Get the /etc/hosts file content of a node.

        Args:
            node: The node name (e.g. "pve1")

        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        hosts = proxmox.nodes(node).hosts.get()
        return json.dumps(hosts, indent=2)

    @mcp.tool()
    def get_node_hardware(node: str) -> str:
        """Get hardware information (PCI devices, USB devices) of a node.

        Args:
            node: The node name (e.g. "pve1")

        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        hardware = proxmox.nodes(node).hardware.get()
        return json.dumps(format_response(hardware), indent=2)

    @mcp.tool()
    def get_node_networks(node: str) -> str:
        """Get network interface configuration of a node.

        Args:
            node: The node name (e.g. "pve1")

        Returns all network interfaces with their configuration (IP, bridge, bond, etc.).
        Permission required: Sys.Audit on /nodes/{node}/network
        """
        proxmox = create_proxmox_client()
        networks = proxmox.nodes(node).network.get()
        return json.dumps(format_response(networks), indent=2)

    @mcp.tool()
    def get_node_storage(node: str) -> str:
        """Get storage information for a node.

        Args:
            node: The node name (e.g. "pve1")

        Returns all storage pools with usage, type, and content information.
        Permission required: Sys.Audit on /storage
        """
        proxmox = create_proxmox_client()
        storage = proxmox.nodes(node).storage.get()
        return json.dumps(format_response(storage), indent=2)
