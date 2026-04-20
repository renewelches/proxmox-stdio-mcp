"""Proxmox MCP Server — STDIO-based MCP server for the Proxmox VE API."""

from mcp.server.fastmcp import FastMCP

from proxmox_mcp.resources import nodes, lxc, qemu, cluster
from proxmox_mcp.tools import lifecycle, updates, tasks

mcp = FastMCP("Proxmox MCP Server")

# Register all resources and tools
nodes.register(mcp)
lxc.register(mcp)
qemu.register(mcp)
cluster.register(mcp)
lifecycle.register(mcp)
updates.register(mcp)
tasks.register(mcp)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
