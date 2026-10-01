# BoxLite + Pi — Confined AI Coding Agent

[BoxLite](https://github.com/boxlite-ai/boxlite) provides hardware-isolated micro-VMs via KVM.
[Pi](https://github.com/earendil-works/pi) is a coding agent CLI. This project runs Pi **inside**
a BoxLite VM — every file read/write, shell command, and LLM tool call is confined to its own
kernel with KVM + seccomp isolation.

```
Host                          BoxLite VM (node:22-slim)
┌──────────┐                  ┌────────────────────────────┐
│  ./pi    ──────────────────→│  pi coding agent            │
│  script  │  boxlite exec    │  (global npm install)       │
│          │                  │                             │
│  files   ←─────────────────→│  /workspace/  (bind mount)  │
└──────────┘                  └────────────────────────────┘
                                KVM + seccomp isolation
```

## Prerequisites

- Linux x86\_64 with `/dev/kvm` accessible
- `jq` installed on the host
- (optional) [LM Studio](https://lmstudio.ai) or another LLM backend reachable from the VM

## Quick start

```bash
git clone https://github.com/pantelisgeorg/boxlited-pi-agent-.git
cd boxlited-pi-agent-

./pi                    # first run: creates VM, installs pi + Python tools
./pi --version          # pass any pi CLI args through
./pi "fix the bug in src/foo.ts"

# Rebuild the VM after changing config or the pi script:
rm -rf .boxlite/ && ./pi
```

First run pulls `node:22-slim`, installs `@earendil-works/pi-coding-agent`, sets up Python 3
with `pdfplumber` and `mcp`, and copies PDF tools into `/opt/pdf-tools/`. Subsequent runs
reuse the cached box.

**Working directory:** The `files/` directory is where you place your task files — it is
the only host directory that the PDF tools and MCP server are scoped to by default.
(Internally the entire repo is mounted at `/workspace` inside the VM, but `MCP_WORKSPACE`
defaults to `/workspace/files`.) Create it if missing and put your project files there.

## Project structure

```
boxlite/
├── .bin/boxlite          BoxLite CLI binary (~95 MB)
├── .boxlite/             VM state — images, disks, config (gitignored)
├── .pi/
│   ├── agent/
│   │   ├── models.json   LLM provider config (LM Studio)
│   │   └── settings.json Pi settings
│   ├── mcp.json          MCP server definitions (built-in MCP)
│   ├── skills/
│   │   └── pdf-tools/    LLM-discoverable PDF tool docs
│   └── mcp-pdf/
│       ├── pdf_server.py       MCP server (MCPServer)
│       ├── pdf-tools-cli.py    CLI wrapper (bash-callable)
│       └── start-pdf-mcp.sh    HTTP bridge for external clients
├── node_modules/         Pi npm package (v0.82.1)
├── sessions/             Pi session logs
├── files/                 Your task files — the only dir mounted into the VM
├── pi                    Entry-point script
├── package.json
└── .gitignore
```

## LLM configuration

Edit `.pi/agent/models.json` to point at your LLM backend. The default uses LM Studio
running on the host at `192.168.1.16:1234`:

```json
{
  "providers": {
    "lmstudio": {
      "baseUrl": "http://192.168.1.16:1234/v1",
      "api": "openai-completions",
      "apiKey": "lm-studio",
      "models": [
        { "id": "qwen/qwen3.5-9b", "name": "qwen3.5-9b" }
      ]
    }
  }
}
```

The model must support tool calling (instruct/chat variants work; base models do not).
`settings.json` sets this as the default provider and model.

## PDF tools

Pi can read and extract data from PDFs in `files/` via the `pdf-tools` CLI.
Commands are available through pi's built-in bash tool:

```bash
pdf-tools read myfile.pdf          # full text, all pages
pdf-tools info myfile.pdf          # page count
pdf-tools text myfile.pdf 3        # extract text from page 3
pdf-tools tables myfile.pdf 1      # tables as markdown
pdf-tools tables myfile.pdf 1 html # tables as HTML
pdf-tools ls                       # list workspace
pdf-tools cat notes.txt            # read text file
pdf-tools write out.txt "content"  # write text file
```

The model discovers these via the **PDF Tools skill** (`.pi/skills/pdf-tools/SKILL.md`),
which documents all commands. Pi auto-loads project-local skills.

### MCP (built-in)

Pi 0.99+ ships built-in MCP support, so the PDF tools can also be exposed as named functions
(`mcp__pdf-tools__pdf_info`, `mcp__pdf-tools__extract_pdf_text`, etc.) in the model's
function list — no third-party adapter needed.

The `.pi/mcp.json` file defines a `pdf-tools` stdio server that runs the Python MCP server
(`.pi/mcp-pdf/pdf_server.py`) inside the VM and scopes it to `/workspace/files`. The `./pi`
wrapper copies it into the VM's user-level config (`~/.pi/agent/mcp.json`) on first setup, so
the tools are available as soon as a session starts.

The tools are registered with `exposure: "direct"`, so they surface directly in the tool
list. To gate them behind search or codemode instead, change `exposure` to `deferred` or
`codemode` (see [pi's MCP docs](https://github.com/earendil-works/pi)). `pi mcp list` shows
connection state and tool names; `/mcp` inspects them inside an interactive session.

The skill-based approach (above) works independently and remains the simplest path when
named-tool exposure isn't needed.

> Note: an earlier `pi-mcp-adapter` approach was blocked by npm registry issues. That package
> now exists, but it is no longer necessary — Pi's built-in MCP covers this use case.

## What's confined

Everything runs inside the VM kernel:

- Pi's file tools (read, write, edit)
- Pi's bash execution (`!` commands, bash tool)
- Pi's grep / find / ls tools
- Any npm / node processes Pi spawns
- The PDF MCP server

The host filesystem is **not accessible** except through the `files/` bind mount.

## VM lifecycle

```bash
./pi                    # start / resume
rm -rf .boxlite/        # destroy VM (rebuilds on next ./pi)
```

The VM persists across runs (stopped but cached). Destroy `.boxlite/` to rebuild from
scratch — do this after changing `models.json`, `settings.json`, or the `pi` script.

## External MCP clients

The PDF MCP server can also be exposed as an HTTP endpoint for VS Code, Claude Desktop,
or the llama.cpp web UI:

```bash
cd .pi/mcp-pdf
./start-pdf-mcp.sh       # listens on http://localhost:8765/mcp
```

This runs on the host using `supergateway` to bridge stdio → HTTP, independently of
the BoxLite VM.
