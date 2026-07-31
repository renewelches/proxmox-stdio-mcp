"""LXC container-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all LXC resources with the MCP server."""

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/lxc")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_node_lxcs(node: str) -> str:
        """List all LXC containers on a specific node with status and resource usage."""
        proxmox = create_proxmox_client()
        lxcs = proxmox.nodes(node).lxc.get()
        return json.dumps(format_response(lxcs), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://lxc")
    @handle_proxmox_error('["perm", "/", ["VM.Audit"]]')
    def get_all_lxcs() -> str:
        """All LXC containers from all nodes in the cluster, grouped by node."""
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        result = {}
        for node_info in nodes:
            node_name = node_info["node"]
            lxcs = proxmox.nodes(node_name).lxc.get()
            result[node_name] = format_response(lxcs)
        return json.dumps(result, indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/lxc/{vmid}/status")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_lxc_status(node: str, vmid: str) -> str:
        """Current status of an LXC container including CPU, memory, network, and disk usage."""
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).lxc(vmid).status.current.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/lxc/{vmid}/config")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_lxc_config(node: str, vmid: str) -> str:
        """Full configuration of an LXC container (CPU, memory, storage, network settings)."""
        proxmox = create_proxmox_client()
        config = proxmox.nodes(node).lxc(vmid).config.get()
        return json.dumps(format_response(config), indent=2)
