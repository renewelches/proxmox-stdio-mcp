"""Import the server and check its registrations without contacting Proxmox.

Catches dependency breakage (e.g. an incompatible mcp release), enforces the
dual-registration rule (every resource must also be exposed as a tool), and
checks that Proxmox errors reach the client instead of MCPServer's generic
"Error executing tool" message.
"""

import asyncio
import sys

from mcp import Client
from mcp.types import TextContent
from proxmoxer.core import ResourceException

import proxmox_mcp.resources.nodes as nodes
from proxmox_mcp.server import mcp


def _forbidden() -> None:
    raise ResourceException(403, "Forbidden", "Permission check failed")


async def main() -> int:
    tools = {t.name for t in await mcp.list_tools()}
    resources = {r.name for r in await mcp.list_resources()}
    resources |= {r.name for r in await mcp.list_resource_templates()}

    if not tools or not resources:
        print("error: server registered no tools or no resources", file=sys.stderr)
        return 1

    missing = sorted(resources - tools)
    if missing:
        print(f"error: resources not also registered as tools: {missing}", file=sys.stderr)
        return 1

    nodes.create_proxmox_client = _forbidden
    async with Client(mcp) as client:
        result = await client.call_tool("get_node_status", {"node": "pve"})
    text = " ".join(c.text for c in result.content if isinstance(c, TextContent))
    if not (result.is_error and "Sys.Audit" in text):
        print(f"error: permission message did not reach the client: {text!r}", file=sys.stderr)
        return 1

    print(f"ok: {len(tools)} tools, {len(resources)} resources, errors surface")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
