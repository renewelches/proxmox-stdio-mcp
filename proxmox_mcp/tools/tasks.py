"""Task tracking tools for monitoring long-running Proxmox operations."""

import json

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.auth import create_proxmox_client
from proxmox_mcp.errors import handle_proxmox_error


def register(mcp: FastMCP) -> None:
    """Register task tracking tools with the MCP server."""

    @mcp.tool()
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_task_status(node: str, upid: str) -> str:
        """Get the status of a Proxmox task by its UPID.

        Use this to check if a previously started operation (VM start, package update,
        etc.) has completed, is still running, or has failed.

        Args:
            node: The node name where the task is running (e.g. "pve1")
            upid: The task UPID returned by a previous operation

        Returns the task status including whether it's running, completed, or failed.
        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        status = proxmox.nodes(node).tasks(upid).status.get()
        return json.dumps(status, indent=2)

    @mcp.tool()
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def get_task_log(node: str, upid: str, start: int = 0, limit: int = 50) -> str:
        """Get the log output of a Proxmox task.

        Useful for seeing the detailed output of operations like package updates.

        Args:
            node: The node name where the task is running (e.g. "pve1")
            upid: The task UPID returned by a previous operation
            start: Starting line number (default: 0)
            limit: Maximum number of lines to return (default: 50)

        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        log = proxmox.nodes(node).tasks(upid).log.get(start=start, limit=limit)
        return json.dumps(log, indent=2)

    @mcp.tool()
    @handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
    def list_node_tasks(node: str, limit: int = 20) -> str:
        """List recent tasks on a node.

        Args:
            node: The node name (e.g. "pve1")
            limit: Maximum number of tasks to return (default: 20)

        Returns a list of recent tasks with their status and type.
        Permission required: Sys.Audit on /nodes/{node}
        """
        proxmox = create_proxmox_client()
        tasks = proxmox.nodes(node).tasks.get(limit=limit)
        return json.dumps(tasks, indent=2)
