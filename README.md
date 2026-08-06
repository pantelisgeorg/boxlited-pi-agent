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
```

First run pulls `node:22-slim`, installs `@earendil-works/pi-coding-agent`, sets up Python 3
with `pdfplumber` and `mcp`, and copies PDF tools into `/opt/pdf-tools/`. Subsequent runs
reuse the cached box.

## Project structure

```
boxlite/
├── .bin/boxlite          BoxLite CLI binary (~95 MB)
├── .boxlite/             VM state — images, disks, config (gitignored)
├── .pi/
│   ├── agent/
│   │   ├── models.json   LLM provider config (LM Studio)
│   │   ├── mcp.json      MCP server definitions
│   │   └── settings.json Pi settings + installed packages
│   └── mcp-pdf/
│       ├── pdf_server.py       MCP server (FastMCP)
│       ├── pdf-tools-cli.py    CLI wrapper (bash-callable)
│       └── start-pdf-mcp.sh    HTTP bridge for external clients
├── node_modules/         Pi npm package (v0.82.1)
├── sessions/             Pi session logs
├── workspace/            Your task files — the only dir mounted into the VM
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

Pi can read and extract data from PDFs in `workspace/` via two mechanisms:

### 1. CLI (always available)

Pi calls these via its bash tool — no MCP needed:

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

### 2. MCP (auto-discovered)

The `pi-mcp-adapter` package (in `settings.json`) reads `mcp.json` on startup and spawns
the Python MCP server. Pi then exposes these as native tools to the LLM:
`pdf_info`, `extract_pdf_text`, `extract_pdf_tables`, `read_pdf`, `list_dir`,
`read_file`, `write_file`.

Both paths share the same Python server and stay confined to `/workspace`.

## What's confined

Everything runs inside the VM kernel:

- Pi's file tools (read, write, edit)
- Pi's bash execution (`!` commands, bash tool)
- Pi's grep / find / ls tools
- Any npm / node processes Pi spawns
- The PDF MCP server

The host filesystem is **not accessible** except through the `workspace/` bind mount.

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
