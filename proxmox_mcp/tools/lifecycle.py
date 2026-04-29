"""Lifecycle management tools for LXC containers and QEMU VMs."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error


def register(mcp: FastMCP) -> None:
    """Register lifecycle tools with the MCP server."""

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_start(node: str, vmid: int) -> str:
        """Start an LXC container.

        WARNING: This will start the container. Make sure this is intentional.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.start.post()
        return json.dumps(
            {"upid": upid, "action": "start", "type": "lxc", "vmid": vmid, "node": node}
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_stop(node: str, vmid: int) -> str:
        """Stop an LXC container immediately (hard stop).

        WARNING: This performs a hard stop. The container will be killed immediately
        without a clean shutdown. Data loss may occur. Consider using lxc_shutdown
        for a graceful shutdown instead.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.stop.post()
        return json.dumps(
            {"upid": upid, "action": "stop", "type": "lxc", "vmid": vmid, "node": node}
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_shutdown(node: str, vmid: int, timeout: int = 60) -> str:
        """Gracefully shut down an LXC container.

        Sends a shutdown signal and waits for the container to stop cleanly.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)
            timeout: Seconds to wait before forcing stop (default: 60)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.shutdown.post(timeout=timeout)
        return json.dumps(
            {
                "upid": upid,
                "action": "shutdown",
                "type": "lxc",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_suspend(node: str, vmid: int) -> str:
        """Suspend (freeze) an LXC container.

        WARNING: The container processes will be frozen. Use lxc_resume to unfreeze.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.suspend.post()
        return json.dumps(
            {
                "upid": upid,
                "action": "suspend",
                "type": "lxc",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_resume(node: str, vmid: int) -> str:
        """Resume a suspended LXC container.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.resume.post()
        return json.dumps(
            {
                "upid": upid,
                "action": "resume",
                "type": "lxc",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def lxc_reboot(node: str, vmid: int, timeout: int = 60) -> str:
        """Reboot an LXC container.

        Performs a graceful reboot of the container.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)
            timeout: Seconds to wait for shutdown before forcing (default: 60)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).lxc(vmid).status.reboot.post(timeout=timeout)
        return json.dumps(
            {
                "upid": upid,
                "action": "reboot",
                "type": "lxc",
                "vmid": vmid,
                "node": node,
            }
        )

    # --- QEMU VM lifecycle tools ---

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_start(node: str, vmid: int) -> str:
        """Start a QEMU virtual machine.

        WARNING: This will start the VM. Make sure this is intentional.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.start.post()
        return json.dumps(
            {
                "upid": upid,
                "action": "start",
                "type": "qemu",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_stop(node: str, vmid: int) -> str:
        """Stop a QEMU VM immediately (hard stop).

        WARNING: This performs a hard stop equivalent to pulling the power cord.
        Data loss may occur. Consider using vm_shutdown for a graceful shutdown instead.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.stop.post()
        return json.dumps(
            {"upid": upid, "action": "stop", "type": "qemu", "vmid": vmid, "node": node}
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_shutdown(node: str, vmid: int, timeout: int = 60) -> str:
        """Gracefully shut down a QEMU virtual machine.

        Sends an ACPI shutdown signal via the QEMU guest agent or ACPI.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)
            timeout: Seconds to wait before forcing stop (default: 60)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.shutdown.post(timeout=timeout)
        return json.dumps(
            {
                "upid": upid,
                "action": "shutdown",
                "type": "qemu",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_suspend(node: str, vmid: int) -> str:
        """Suspend a QEMU virtual machine.

        WARNING: The VM state will be paused. Use vm_resume to continue execution.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.suspend.post()
        return json.dumps(
            {
                "upid": upid,
                "action": "suspend",
                "type": "qemu",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_resume(node: str, vmid: int) -> str:
        """Resume a suspended QEMU virtual machine.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.resume.post()
        return json.dumps(
            {
                "upid": upid,
                "action": "resume",
                "type": "qemu",
                "vmid": vmid,
                "node": node,
            }
        )

    @mcp.tool()
    @handle_proxmox_error('["perm", "/vms/{vmid}", ["VM.PowerMgmt"]]')
    def vm_reboot(node: str, vmid: int, timeout: int = 60) -> str:
        """Reboot a QEMU virtual machine.

        Performs a graceful reboot via ACPI.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)
            timeout: Seconds to wait for shutdown before forcing (default: 60)

        Returns the task UPID for tracking the operation.
        Permission required: VM.PowerMgmt on /vms/{vmid}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).qemu(vmid).status.reboot.post(timeout=timeout)
        return json.dumps(
            {
                "upid": upid,
                "action": "reboot",
                "type": "qemu",
                "vmid": vmid,
                "node": node,
            }
        )
