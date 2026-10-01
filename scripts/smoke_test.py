"""Import the server and check its registrations without contacting Proxmox.

Catches dependency breakage (e.g. an incompatible mcp release) and enforces
the dual-registration rule: every resource must also be exposed as a tool.
"""

import asyncio
import sys

from proxmox_mcp.server import mcp


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

    print(f"ok: {len(tools)} tools, {len(resources)} resources")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
