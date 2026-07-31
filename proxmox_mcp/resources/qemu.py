"""QEMU VM-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all QEMU/VM resources with the MCP server."""

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/qemu")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_node_vms(node: str) -> str:
        """List all QEMU virtual machines on a specific node with status and resource usage."""
        proxmox = create_proxmox_client()
        vms = proxmox.nodes(node).qemu.get()
        return json.dumps(format_response(vms), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://qemu")
    @handle_proxmox_error('["perm", "/", ["VM.Audit"]]')
    def get_all_vms() -> str:
        """All QEMU virtual machines from all nodes in the cluster, grouped by node."""
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        result = {}
        for node_info in nodes:
            node_name = node_info["node"]
            vms = proxmox.nodes(node_name).qemu.get()
            result[node_name] = format_response(vms)
        return json.dumps(result, indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/qemu/{vmid}/status")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_vm_status(node: str, vmid: str) -> str:
        """Current status of a QEMU VM including CPU, memory, network, and disk usage."""
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).qemu(vmid).status.current.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    @mcp.resource("proxmox://nodes/{node}/qemu/{vmid}/config")
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.Audit"]]')
    def get_vm_config(node: str, vmid: str) -> str:
        """Full configuration of a QEMU VM (CPU, memory, storage, network settings)."""
        proxmox = create_proxmox_client()
        config = proxmox.nodes(node).qemu(vmid).config.get()
        return json.dumps(format_response(config), indent=2)
