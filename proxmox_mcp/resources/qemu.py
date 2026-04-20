"""QEMU VM-related MCP resources."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.formatting import format_response


def register(mcp: FastMCP) -> None:
    """Register all QEMU/VM resources with the MCP server."""

    @mcp.tool()
    def get_node_vms(node: str) -> str:
        """Get all QEMU virtual machines on a specific node.

        Args:
            node: The node name (e.g. "pve1")

        Returns a list of VMs with their status, CPU/memory usage, etc.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        vms = proxmox.nodes(node).qemu.get()
        return json.dumps(format_response(vms), indent=2)

    @mcp.tool()
    def get_all_vms() -> str:
        """Get all QEMU virtual machines from all nodes in the cluster.

        Returns VMs grouped by node name.
        Permission required: VM.Audit on /vms/{vmid}, Sys.Audit on /
        """
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        result = {}
        for node_info in nodes:
            node_name = node_info["node"]
            vms = proxmox.nodes(node_name).qemu.get()
            result[node_name] = format_response(vms)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_vm_status(node: str, vmid: int) -> str:
        """Get the current status of a QEMU virtual machine.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns detailed status including CPU, memory, network, and disk usage.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).qemu(vmid).status.current.get()
        return json.dumps(format_response(status), indent=2)

    @mcp.tool()
    def get_vm_config(node: str, vmid: int) -> str:
        """Get the configuration of a QEMU virtual machine.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns the full configuration including CPU, memory, storage, and network settings.
        Permission required: VM.Audit on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        config = proxmox.nodes(node).qemu(vmid).config.get()
        return json.dumps(format_response(config), indent=2)
