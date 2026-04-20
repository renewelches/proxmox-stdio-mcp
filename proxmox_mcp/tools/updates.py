"""Package update tools for nodes, LXC containers, and QEMU VMs."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client

ALLOWED_COMMANDS = ["apt-get update", "apt-get upgrade -y", "apt-get dist-upgrade -y"]


def _validate_command(command: str) -> None:
    """Ensure only whitelisted apt commands are executed."""
    normalized = " ".join(command.strip().split())
    if normalized not in ALLOWED_COMMANDS:
        raise ValueError(
            f"Command not allowed: '{command}'. "
            f"Only the following commands are permitted: {', '.join(ALLOWED_COMMANDS)}"
        )


def register(mcp: FastMCP) -> None:
    """Register package update tools with the MCP server."""

    @mcp.tool()
    def node_apt_update(node: str) -> str:
        """Update the package index on a Proxmox node (equivalent to 'apt-get update').

        WARNING: This modifies the package database on the node. Ensure you have
        proper authorization before running this.

        Args:
            node: The node name (e.g. "pve1")

        Returns the task UPID for tracking the operation.
        Permission required: Sys.Modify on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        upid = proxmox.nodes(node).apt.update.post()
        return json.dumps({"upid": upid, "action": "apt-update", "node": node})

    @mcp.tool()
    def node_apt_list_upgrades(node: str) -> str:
        """List available package upgrades on a Proxmox node.

        Args:
            node: The node name (e.g. "pve1")

        Returns a list of packages that can be upgraded.
        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        # First refresh the package index
        proxmox.nodes(node).apt.update.post()
        # Then list available updates
        updates = proxmox.nodes(node).apt.update.get()
        return json.dumps(updates, indent=2)

    @mcp.tool()
    def update_all_nodes() -> str:
        """Update the package index on ALL nodes in the cluster.

        WARNING: This will run 'apt-get update' on every node in the cluster.
        This is a cluster-wide operation. Make sure this is intentional.

        Returns task UPIDs for each node for tracking.
        Permission required: Sys.Modify on /nodes/{node} for each node
        """
        proxmox = create_proxmox_client()
        nodes = proxmox.nodes.get()
        results = []
        for node_info in nodes:
            node_name = node_info["node"]
            upid = proxmox.nodes(node_name).apt.update.post()
            results.append({"node": node_name, "upid": upid, "action": "apt-update"})
        return json.dumps(results, indent=2)

    @mcp.tool()
    def lxc_exec_update(node: str, vmid: int, command: str = "apt-get update") -> str:
        """Execute a package update command inside an LXC container.

        WARNING: This executes a command inside the container. Only apt update/upgrade
        commands are allowed.

        Allowed commands:
        - "apt-get update"
        - "apt-get upgrade -y"
        - "apt-get dist-upgrade -y"

        Prerequisites: The LXC container must be running.

        Args:
            node: The node name (e.g. "pve1")
            vmid: The container ID (e.g. 100)
            command: The apt command to run (default: "apt-get update")

        Permission required: VM.Console on /vms/{vmid}
        """
        _validate_command(command)
        proxmox = create_proxmox_client()
        parts = command.split()
        result = proxmox.nodes(node).lxc(vmid).exec.post(command=parts)
        return json.dumps(
            {
                "action": "lxc-exec",
                "node": node,
                "vmid": vmid,
                "command": command,
                "result": result,
            },
            indent=2,
        )

    @mcp.tool()
    def vm_exec_update(node: str, vmid: int, command: str = "apt-get update") -> str:
        """Execute a package update command inside a QEMU VM via the guest agent.

        WARNING: This executes a command inside the VM. Only apt update/upgrade
        commands are allowed.

        Allowed commands:
        - "apt-get update"
        - "apt-get upgrade -y"
        - "apt-get dist-upgrade -y"

        Prerequisites:
        - The VM must be running
        - The QEMU guest agent (qemu-guest-agent) must be installed and running inside the VM
        - The VM configuration must have the guest agent enabled (agent: 1)

        Args:
            node: The node name (e.g. "pve1")
            vmid: The VM ID (e.g. 100)
            command: The apt command to run (default: "apt-get update")

        Permission required: VM.Console on /vms/{vmid}
        """
        _validate_command(command)
        proxmox = create_proxmox_client()
        parts = command.split()
        result = (
            proxmox.nodes(node)
            .qemu(vmid)
            .agent.exec.post(
                command=parts[0], **{"input-data": "", "arguments": parts[1:]}
            )
        )
        return json.dumps(
            {
                "action": "vm-agent-exec",
                "node": node,
                "vmid": vmid,
                "command": command,
                "result": result,
            },
            indent=2,
        )
