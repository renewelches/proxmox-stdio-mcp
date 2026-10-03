"""Proxmox MCP Server — STDIO-based MCP server for the Proxmox VE API."""

from importlib.metadata import version

from mcp.server.mcpserver import MCPServer

from proxmox_mcp.resources import cluster, lxc, nodes, qemu
from proxmox_mcp.tools import lifecycle, tasks, updates

# Report the installed package version, so pyproject.toml stays the single source.
mcp = MCPServer("Proxmox MCP Server", version=version("proxmox-mcp"))

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
