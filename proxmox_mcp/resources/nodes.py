"""Node-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all node resources with the MCP server."""

    @mcp.tool()
    @mcp.resource("proxmox://nodes")
    @handle_proxmox_error('["perm", "/", ["Sys.Audit"]]')
    def get_nodes() -> str:
        """List all nodes in the Proxmox cluster with status, CPU/memory usage, and uptime."""
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        return json.dumps(format_response(nodes), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/status")
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_node_status(node: str) -> str:
        """Detailed node status: CPU, memory, swap, filesystem, kernel version, load averages."""
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).status.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/hosts")
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_node_hosts(node: str) -> str:
        """Contents of /etc/hosts on a node."""
        proxmox = create_proxmox_client()
        hosts = proxmox.nodes(node).hosts.get()
        return json.dumps(hosts, indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/hardware")
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_node_hardware(node: str) -> str:
        """Hardware information (PCI devices, USB devices) of a node."""
        proxmox = create_proxmox_client()
        hardware = proxmox.nodes(node).hardware.get()
        return json.dumps(format_response(hardware), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/network")
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_node_networks(node: str) -> str:
        """Network interface configuration (IP, bridge, bond, etc.) of a node."""
        proxmox = create_proxmox_client()
        networks = proxmox.nodes(node).network.get()
        return json.dumps(format_response(networks), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/storage")
    @handle_proxmox_error('["perm", "/storage/{storage}", ["Datastore.Audit"]]')
    def get_node_storage(node: str) -> str:
        """Storage pools with usage, type, and content information for a node."""
        proxmox = create_proxmox_client()
        storage = proxmox.nodes(node).storage.get()
        return json.dumps(format_response(storage), indent=2)
