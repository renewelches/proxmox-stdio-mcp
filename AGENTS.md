# AGENTS.md

Instructions for AI coding agents working in this repository. Humans: see
[README.md](README.md).

proxmox-mcp is a STDIO-based MCP server that exposes the Proxmox VE API to
AI assistants. It uses `proxmoxer` for API access and `mcp[cli]` (FastMCP)
for the MCP protocol, and runs as the CLI entry point `proxmox-mcp`. It
holds Proxmox credentials and can start, stop, and update guests, so treat
security as the default concern in every change.

## Commands

Use the Makefile targets; CI runs the same ones.

| Task | Command |
|---|---|
| Install dependencies | `make sync` |
| Run the server | `make run` |
| Format (and autofix lint) | `make fmt` |
| Format check | `make fmt-check` |
| Lint (ruff) | `make lint` |
| Type check (mypy) | `make typecheck` |
| Smoke test | `make smoke` |
| Vulnerability scan (pip-audit) | `make vuln` |
| Check `uv.lock` is current | `make lock-check` |
| Everything CI runs | `make check` |
| Build wheel and sdist | `make build` |

Always use `uv` — never `pip`. Use modern `uv` commands (`uv add`,
`uv sync`, `uv lock`, `uv tool`), not legacy `uv pip` equivalents. Dev tools
(ruff, mypy, pip-audit) are in the `dev` dependency group, so `uv sync`
installs them.

There is no unit test suite. `make smoke` imports the server, lists its
registrations without contacting Proxmox, and fails if any resource is not
also registered as a tool.

## Layout

- `proxmox_mcp/server.py` — entry point. Creates the `FastMCP` instance and
  registers all modules.
- `proxmox_mcp/auth.py` — builds the `ProxmoxAPI` client from env vars.
  Supports password or API token auth.
- `proxmox_mcp/formatting.py` — converts raw API byte/uptime values to
  human-readable strings.
- `proxmox_mcp/errors.py` — `handle_proxmox_error(required_permission)`
  decorator. Catches `proxmoxer.core.ResourceException` and converts
  403/401/404/500 into clear messages naming the missing Proxmox permission.
- `proxmox_mcp/resources/` — read-only GET operations (nodes, LXC, QEMU,
  cluster). Each module has a `register(mcp)` function.
- `proxmox_mcp/tools/` — mutation operations: lifecycle (start/stop/reboot),
  package updates, task tracking. Same `register(mcp)` pattern.
- `scripts/smoke_test.py` — the `make smoke` check.

`mcp` is capped below 2: mcp 2.x renamed `FastMCP` and changed its APIs.
Moving to 2.x is a migration, not a dependency bump; do not lift the cap
without the user asking for it.

## Resources vs Tools — strict rule

**GET operations MUST be MCP resources (`@mcp.resource()`), and additionally
registered as tools.**

- Use `@mcp.resource("proxmox://some/uri")` for any read-only Proxmox API
  call (HTTP GET).
- Use `@mcp.resource("proxmox://path/{param}/sub")` with URI template
  parameters for parameterised reads. URI params must exactly match function
  parameter names. They arrive as `str` regardless of Proxmox type — do not
  type-hint them as `int`.
- Mutating operations (POST/PUT/DELETE) get `@mcp.tool()` only — never a
  resource.

This maps directly onto the MCP spec: resources are safe, idempotent reads;
tools are effectful actions.

### Dual registration of reads — deliberate, do not "fix"

Every read-only function also carries `@mcp.tool()` stacked **above** its
`@mcp.resource()`:

```python
@mcp.tool()
@mcp.resource("proxmox://nodes/{node}/status")
@handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
def get_node_status(node: str) -> str:
    ...
```

Claude Desktop and Claude Code do not autonomously read MCP resources — the
user must attach them by hand. Without the tool registration these reads are
unreachable to the model. The resource stays the canonical definition; the
tool is the access path. Do not remove the `@mcp.tool()` lines from
`resources/`.

Tool names come from the bare function name, so names in `resources/` must
not collide with names in `tools/`.

## Error handling

Every resource function and tool must be decorated with
`@handle_proxmox_error(permission)` from `proxmox_mcp/errors.py`, where
`permission` is the Proxmox permission check string for that endpoint, e.g.
`'["perm", "/vms/{vmid}", ["VM.Audit"]]'`. Look up the exact check in the
[Proxmox API viewer](https://pve.proxmox.com/pve-docs/api-viewer/).

Decorator order matters — `@mcp.resource()` or `@mcp.tool()` must be
outermost:

```python
@mcp.resource("proxmox://nodes/{node}/status")
@handle_proxmox_error('["perm", "/nodes/{node}", ["Sys.Audit"]]')
def get_node_status(node: str) -> str:
    ...
```

## Adding new endpoints

1. **Read-only (GET):** add to a module in `resources/`, use
   `@mcp.tool()` + `@mcp.resource()` + `@handle_proxmox_error()`.
2. **Mutating (POST/PUT/DELETE):** add to a module in `tools/`, use
   `@mcp.tool()` + `@handle_proxmox_error()`.
3. Implement `register(mcp: FastMCP)` and import/call it in `server.py`.

## Vulnerability policy

`make vuln` runs pip-audit against the runtime dependencies pinned in
`uv.lock` (dev tools are excluded; they do not ship). Unlike govulncheck,
pip-audit has no reachability analysis: **every finding fails the scan.**

### At the start of a session

Before starting the requested task, run `make vuln` once. If it reports
vulnerabilities, tell the user in your first reply, list the package, found
version, and fixed version for each, and offer to fix them. Do not fix them
unasked in the middle of an unrelated task.

### Before every commit

Run `make check` (format, lint, lock, type check, smoke test, vulnerability
scan) and do not commit unless it passes.

If `make vuln` reports vulnerabilities, fix them in the same change:

1. For each affected package,
   `uv lock --upgrade-package <package>==<fixed version>`, using the fix
   version from the report. This works for transitive packages too, as long
   as no declared constraint excludes the fixed version.
2. If the package is a direct dependency, also raise its lower bound in
   `pyproject.toml` to the fixed version, so fresh installs (`uvx`,
   `uv tool install`) cannot resolve a vulnerable release.
3. Re-run `make check`.
4. Commit the `pyproject.toml`/`uv.lock` changes and tell the user which
   packages moved, from which version to which.

**Stop and ask the user instead** when no fixed version exists, the fix
requires a new major version of a direct dependency (or lifting a declared
cap such as `mcp<2`), or the upgrade breaks type checking or the smoke test.
Never silence a finding with `--ignore-vuln`, pin around it, or skip the
scan without the user's explicit approval.

If `make vuln` cannot run (offline, tool missing), say so; do not report
the change as scanned.

## Security rules

- Never log, print, or include in errors or tool output: Proxmox passwords,
  API token secrets, or ticket/CSRF values.
- Never commit `.envrc` or `.env`; they hold live Proxmox credentials and are
  gitignored. Do not read them back to the user or into tool output.
- Do not weaken TLS verification defaults (`PROXMOX_VERIFY_SSL`) or the
  permission checks in `handle_proxmox_error` without the user asking for it
  explicitly.
- Mutating tools act on real infrastructure. Do not add tools that delete
  guests, storage, or snapshots without the user asking for that endpoint.

## Workflow

Trunk-based: `main` is the only long-lived branch and is protected.

- Branch from `main` for every change, using a short-lived branch named
  `<type>/<topic>` (e.g. `feat/storage-resources`, `ci/release-signing`),
  and merge back through a pull request once CI passes. Merged branches are
  deleted automatically.
- Do not create `dev`, `develop`, or release branches.
- Releases are cut from `main` by tagging: bump `version` in
  `pyproject.toml` in a PR, merge it, then push a `vX.Y.Z` tag that matches
  it. The release workflow builds, signs (cosign, keyless), attests, and
  publishes. Run it manually (`workflow_dispatch`) for a dry run.

## Commits

Conventional Commits with a scope where it fits: `feat(resources): ...`,
`fix(auth): ...`, `docs: ...`, `build: ...`, `ci: ...`. Imperative mood,
lowercase summary. Keep dependency bumps in their own commit when they are
not required by the change itself.
