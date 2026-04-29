# Proxmox MCP Server

An STDIO-based [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for the [Proxmox VE API](https://pve.proxmox.com/pve-docs/api-viewer/). Enables AI assistants like Claude to query and manage your Proxmox cluster through a standardized interface. Supports a subset of the Proxmox API focused on common operations; see [Available Tools](#available-tools) for full coverage.

## Features

- **Node Management** — List nodes, view status, hardware, hosts, networks, and storage
- **LXC Containers** — List, inspect, start/stop/reboot, and run package updates
- **QEMU VMs** — List, inspect, start/stop/reboot, and run package updates via guest agent
- **Cluster Overview** — Quick cluster health and quorum status
- **Task Tracking** — Monitor long-running operations (updates, reboots, etc.)
- **Human-Readable Output** — Byte values (memory, disk) are automatically converted to GB/MB/KB

## Prerequisites

- Python 3.10+
- A Proxmox VE cluster (version 7.x or 8.x)
- An API token or user credentials with appropriate permissions

### For VM Package Updates

The QEMU guest agent must be installed and running inside VMs that you want to manage with `vm_exec_update`:

1. Install inside the VM: `apt-get install qemu-guest-agent`
2. Enable in VM config (Proxmox UI: Options > QEMU Guest Agent > Enable)
3. Start the agent: `systemctl enable --now qemu-guest-agent`

### For LXC Package Updates

LXC containers support command execution natively through the Proxmox API. No additional agent is needed, but the container must be running.

## Installation

Requires [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone <repository-url>
cd proxmox-stdio-mcp

# Install dependencies
uv sync

# Run the server
uv run proxmox-mcp
```

## Configuration

### Environment Variables

| Variable               | Required | Description                                                           |
| ---------------------- | -------- | --------------------------------------------------------------------- |
| `PROXMOX_HOST`         | Yes      | Proxmox host (e.g. `pve.example.com` or `https://192.168.1.100:8006`) |
| `PROXMOX_PORT`         | No       | API port (default: `8006`)                                            |
| `PROXMOX_USER`         | Auth     | Username (e.g. `root@pam`)                                            |
| `PROXMOX_PASSWORD`     | Auth     | Password                                                              |
| `PROXMOX_TOKEN_ID`     | Auth     | API token ID (e.g. `user@pam!my-token`)                               |
| `PROXMOX_TOKEN_SECRET` | Auth     | API token secret                                                      |
| `PROXMOX_VERIFY_SSL`   | No       | SSL verification: `true` or `false` (default: `true`)                 |

### Authentication Priority

If both username/password and API token are configured, **username/password takes precedence**.

### Creating an API Token (Recommended)

```bash
# In the Proxmox UI: Datacenter > Permissions > API Tokens > Add
# Or via CLI on a Proxmox node:
pveum user token add root@pam mcp-token --privsep 0
```

> **Note:** Setting `--privsep 0` gives the token the same permissions as the user. For production use, create a dedicated user with minimal permissions (see below).

### MCP Client Configuration

#### Claude Desktop / Claude Code

Add to your MCP settings (`claude_desktop_config.json` or `.mcp.json`):

##### Option 1: Development (Using uv)

For active development or when running directly from the project directory:

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/proxmox-stdio-mcp",
        "run",
        "proxmox-mcp"
      ],
      "env": {
        "PROXMOX_HOST": "https://pve.example.com:8006",
        "PROXMOX_TOKEN_ID": "user@pam!mcp-token",
        "PROXMOX_TOKEN_SECRET": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "PROXMOX_VERIFY_SSL": "false"
      }
    }
  }
}
```

##### Option 2: Installed Package (Using Wheel)

For a distributed or installed version:

1. Build the wheel:

```bash
uv build
```

1. Install it:

```bash
uv tool install dist/proxmox_mcp-0.1.0-py3-none-any.whl
```

1. Update your MCP config:

```json
{
  "mcpServers": {
    "proxmox": {
      "command": "proxmox-mcp",
      "env": {
        "PROXMOX_HOST": "https://pve.example.com:8006",
        "PROXMOX_TOKEN_ID": "user@pam!mcp-token",
        "PROXMOX_TOKEN_SECRET": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "PROXMOX_VERIFY_SSL": "false"
      }
    }
  }
}
```

Replace the placeholder values with your actual Proxmox configuration.

##### Option 3: Claude Code CLI (`claude mcp add`)

The Claude Code CLI can register the server directly from the wheel — no separate install step required:

```bash
claude mcp add proxmox \
  -e PROXMOX_HOST=https://pve.example.com:8006 \
  -e PROXMOX_TOKEN_ID=user@pam!mcp-token \
  -e PROXMOX_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  -e PROXMOX_VERIFY_SSL=false \
  -- uvx --from /path/to/dist/proxmox_mcp-0.1.0-py3-none-any.whl proxmox-mcp
```

`uvx --from` installs the wheel into an isolated environment on first run and caches it — no virtual environment management needed.

Alternatively, install the wheel as a persistent `uv` tool first:

```bash
uv tool install /path/to/dist/proxmox_mcp-0.1.0-py3-none-any.whl
```

Then register it with Claude Code:

```bash
claude mcp add proxmox \
  -e PROXMOX_HOST=https://pve.example.com:8006 \
  -e PROXMOX_TOKEN_ID=user@pam!mcp-token \
  -e PROXMOX_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  -e PROXMOX_VERIFY_SSL=false \
  -- proxmox-mcp
```

Verify the server is registered: `claude mcp list`

By default, `claude mcp add` registers the server at user scope (`~/.claude/claude_desktop_config.json`). Pass `--scope project` to register it in `.mcp.json` in the current directory instead (useful for project-specific setups checked into version control).

## Required Permissions

### Minimal Read-Only (Resources Only)

For listing and inspecting nodes, VMs, and containers:

| Permission        | Path               | Used By                                                                              |
| ----------------- | ------------------ | ------------------------------------------------------------------------------------ |
| `Sys.Audit`       | `/`                | `proxmox://nodes`, `proxmox://cluster/status`, `proxmox://lxc`, `proxmox://qemu`    |
| `Sys.Audit`       | `/nodes/{node}`    | `proxmox://nodes/{node}/status`, `.../hosts`, `.../hardware`, `.../network`          |
| `Datastore.Audit` | `/storage/{storage}` | `proxmox://nodes/{node}/storage`                                                   |
| `VM.Audit`        | `/vms/{vmid}`      | `proxmox://nodes/{node}/lxc`, `.../lxc/{vmid}/status`, `.../lxc/{vmid}/config`, same for qemu |

### Lifecycle Management (Start/Stop/Reboot)

| Permission     | Path          | Used By                                                                                                                                                          |
| -------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VM.PowerMgmt` | `/vms/{vmid}` | `lxc_start`, `lxc_stop`, `lxc_shutdown`, `lxc_suspend`, `lxc_resume`, `lxc_reboot`, `vm_start`, `vm_stop`, `vm_shutdown`, `vm_suspend`, `vm_resume`, `vm_reboot` |

### Package Updates

| Permission   | Path            | Used By                               |
| ------------ | --------------- | ------------------------------------- |
| `Sys.Modify` | `/nodes/{node}` | `node_apt_update`, `refresh_apt_index_all_nodes` |
| `Sys.Audit`  | `/nodes/{node}` | `node_apt_list_upgrades`              |
| `VM.Console` | `/vms/{vmid}`   | `lxc_exec_update`, `vm_exec_update`   |

### Task Tracking

| Permission  | Path            | Used By                                              |
| ----------- | --------------- | ---------------------------------------------------- |
| `Sys.Audit` | `/nodes/{node}` | `get_task_status`, `get_task_log`, `list_node_tasks` |

### Example: Creating a Minimal-Permission User

```bash
# Create a dedicated user
pveum user add mcp@pve

# Create a role with read-only permissions
pveum role add MCPReadOnly -privs "Sys.Audit,VM.Audit"

# Create a role with full MCP permissions
pveum role add MCPFull -privs "Sys.Audit,Sys.Modify,VM.Audit,VM.PowerMgmt,VM.Console"

# Assign the role (use MCPReadOnly or MCPFull)
pveum aclmod / -user mcp@pve -role MCPFull

# Create an API token
pveum user token add mcp@pve mcp-token --privsep 0
```

## Available Resources & Tools

### Resources (Read-Only)

All read-only GET operations are exposed as [MCP resources](https://spec.modelcontextprotocol.io/specification/2025-03-26/server/resources/) with URI templates, not tools. This gives clients semantic clarity (safe reads vs. effectful actions), caching, and discoverability.

| URI                                          | Description                                           |
| -------------------------------------------- | ----------------------------------------------------- |
| `proxmox://nodes`                            | List all nodes in the cluster                         |
| `proxmox://nodes/{node}/status`              | Detailed status of a node (CPU, memory, load)         |
| `proxmox://nodes/{node}/hosts`               | Contents of `/etc/hosts` on a node                    |
| `proxmox://nodes/{node}/hardware`            | Hardware info (PCI, USB devices)                      |
| `proxmox://nodes/{node}/network`             | Network interface configuration                       |
| `proxmox://nodes/{node}/storage`             | Storage pools and usage                               |
| `proxmox://cluster/status`                   | Cluster health and quorum status                      |
| `proxmox://nodes/{node}/lxc`                 | LXC containers on a specific node                     |
| `proxmox://lxc`                              | All LXC containers across all nodes (grouped by node) |
| `proxmox://nodes/{node}/lxc/{vmid}/status`   | Current status of an LXC container                    |
| `proxmox://nodes/{node}/lxc/{vmid}/config`   | Configuration of an LXC container                     |
| `proxmox://nodes/{node}/qemu`                | QEMU VMs on a specific node                           |
| `proxmox://qemu`                             | All VMs across all nodes (grouped by node)            |
| `proxmox://nodes/{node}/qemu/{vmid}/status`  | Current status of a VM                                |
| `proxmox://nodes/{node}/qemu/{vmid}/config`  | Configuration of a VM                                 |

### Lifecycle Management

| Tool           | Description                           |
| -------------- | ------------------------------------- |
| `lxc_start`    | Start an LXC container                |
| `lxc_stop`     | Hard stop an LXC container            |
| `lxc_shutdown` | Graceful shutdown of an LXC container |
| `lxc_suspend`  | Suspend (freeze) an LXC container     |
| `lxc_resume`   | Resume a suspended LXC container      |
| `lxc_reboot`   | Reboot an LXC container               |
| `vm_start`     | Start a QEMU VM                       |
| `vm_stop`      | Hard stop a QEMU VM                   |
| `vm_shutdown`  | Graceful shutdown of a QEMU VM        |
| `vm_suspend`   | Suspend a QEMU VM                     |
| `vm_resume`    | Resume a suspended QEMU VM            |
| `vm_reboot`    | Reboot a QEMU VM                      |

### Package Updates

| Tool                     | Description                                         |
| ------------------------ | --------------------------------------------------- |
| `node_apt_update`        | Run `apt-get update` on a node                      |
| `node_apt_list_upgrades` | List available package upgrades on a node           |
| `refresh_apt_index_all_nodes` | Run `apt-get update` on all nodes (refreshes apt index only — does not upgrade) |
| `lxc_exec_update`        | Run apt commands inside an LXC container            |
| `vm_exec_update`         | Run apt commands inside a VM (requires guest agent) |

### Task Tracking

| Tool              | Description                            |
| ----------------- | -------------------------------------- |
| `get_task_status` | Check status of a running task by UPID |
| `get_task_log`    | Get log output of a task               |
| `list_node_tasks` | List recent tasks on a node            |

## Security Notes

- **Command Whitelist**: The `lxc_exec_update` and `vm_exec_update` tools only allow these commands:
  - `apt-get update`
  - `apt-get upgrade -y`
  - `apt-get dist-upgrade -y`

  All other commands are rejected.

- **Destructive Operations**: Tools that stop, shutdown, or reboot VMs/containers include warnings in their descriptions. The MCP client (e.g. Claude) should confirm with the user before executing these.

- **SSL Verification**: Enabled by default. Set `PROXMOX_VERIFY_SSL=false` only for self-signed certificates in trusted environments.

## Error Handling

All resources and tools include permission-aware error handling. When the API token lacks a required privilege, the error message tells you exactly which Proxmox permission is missing:

```
Permission denied: ["perm", "/vms/100", ["VM.PowerMgmt"]] — ensure the API token/user has this privilege.
```

Other error types (401 auth failure, 404 not found, 500 server error) also return clear, actionable messages.

## Extending

The server is designed to be extended with additional Proxmox API endpoints. To add new functionality:

1. Create a new module in `proxmox_mcp/resources/` (for read-only `@mcp.resource()`) or `proxmox_mcp/tools/` (for mutations via `@mcp.tool()`)
2. Implement a `register(mcp: FastMCP)` function
3. Wrap each function with `@handle_proxmox_error('["perm", "/path", ["Required.Privilege"]]')`
4. Import and register it in `proxmox_mcp/server.py`

## License

MIT
