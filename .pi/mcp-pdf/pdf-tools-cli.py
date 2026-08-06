#!/usr/bin/env python3
"""CLI wrapper for PDF tools — callable via bash from pi inside the BoxLite VM.

Usage:
  pdf-tools info <path>              # page count
  pdf-tools text <path> <page>       # extract text from a page
  pdf-tools tables <path> <page> [fmt]  # extract tables (markdown|html)
  pdf-tools read <path>              # full PDF text (all pages)
  pdf-tools ls [subpath]             # list workspace dir
  pdf-tools cat <path>               # read text file
  pdf-tools write <path> <content>   # write text file
"""

import os
import sys
from pathlib import Path

import pdfplumber

WORKSPACE = Path(
    os.environ.get("MCP_WORKSPACE", "/workspace")
).resolve()


def safe(path: str) -> Path | None:
    raw = str(path)
    if raw.startswith("/workspace/"):
        raw = raw[len("/workspace/"):]
    elif raw == "/workspace":
        raw = "."
    p = (WORKSPACE / raw).resolve()
    if p != WORKSPACE and WORKSPACE not in p.parents:
        return None
    return p


def cmd_info(path):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    if not p.is_file():
        return f"Error: '{path}' is not a file in the workspace"
    with pdfplumber.open(str(p)) as pdf:
        return f"{p.relative_to(WORKSPACE)}: {len(pdf.pages)} pages"


def cmd_text(path, page):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    if not p.is_file():
        return f"Error: '{path}' is not a file in the workspace"
    with pdfplumber.open(str(p)) as pdf:
        if page < 1 or page > len(pdf.pages):
            return f"Error: page {page} out of range (1..{len(pdf.pages)})"
        return pdf.pages[page - 1].extract_text() or "(no extractable text on this page)"


def _merge_complementary_columns(grid):
    while grid and len(grid[0]) > 1:
        width = len(grid[0])
        for i in range(width - 1):
            if all(not (r[i] and r[i + 1]) for r in grid):
                grid = [r[:i] + [(r[i] or r[i + 1])] + r[i + 2:] for r in grid]
                break
        else:
            break
    return grid


def _clean_grid(rows):
    grid = [[(c if c is not None else "").replace("\n", " ").strip() for c in row]
            for row in rows if row and any((c or "").strip() for c in row)]
    if not grid:
        return []
    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]
    keep = [i for i in range(width) if any(r[i] for r in grid)]
    grid = [[r[i] for i in keep] for r in grid]
    return _merge_complementary_columns(grid)


def _grid_to_markdown(grid):
    width = len(grid[0])
    header, *body = grid
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def cmd_tables(path, page, fmt="markdown"):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    if not p.is_file():
        return f"Error: '{path}' is not a file in the workspace"
    if fmt not in ("markdown", "html"):
        return f"Error: fmt must be 'markdown' or 'html', got '{fmt}'"
    with pdfplumber.open(str(p)) as pdf:
        if page < 1 or page > len(pdf.pages):
            return f"Error: page {page} out of range (1..{len(pdf.pages)})"
        raw = pdf.pages[page - 1].extract_tables()
    grids = [g for g in (_clean_grid(t) for t in raw) if len(g) >= 2 and len(g[0]) >= 2]
    if not grids:
        return "(no real table on this page — it may be prose; try 'pdf-tools text')"
    blocks = [f"### Table {i}\n\n{_grid_to_markdown(g)}" for i, g in enumerate(grids, 1)]
    return "\n\n".join(blocks)


def cmd_read(path):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    if not p.is_file():
        return f"Error: '{path}' is not a file in the workspace"
    with pdfplumber.open(str(p)) as pdf:
        parts = [
            f"--- page {i} ---\n{(page.extract_text() or '').strip()}"
            for i, page in enumerate(pdf.pages, 1)
        ]
    return "\n\n".join(parts) or "(no extractable text)"


def cmd_ls(subpath="."):
    d = safe(subpath)
    if d is None:
        return f"Error: '{subpath}' is outside the confined workspace"
    if not d.exists():
        return f"Error: '{subpath}' does not exist in the workspace"
    if not d.is_dir():
        return f"Error: '{subpath}' is not a directory"
    rows = []
    for e in sorted(d.iterdir()):
        kind = "dir " if e.is_dir() else "file"
        size = e.stat().st_size if e.is_file() else ""
        rows.append(f"{kind}  {e.relative_to(WORKSPACE)}  {size}")
    return "\n".join(rows) or "(empty)"


def cmd_cat(path):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    if not p.is_file():
        return f"Error: '{path}' is not a file in the workspace"
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: '{path}' is not UTF-8 text (binary file?)"


def cmd_write(path, content):
    p = safe(path)
    if p is None:
        return f"Error: '{path}' is outside the confined workspace"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {p.relative_to(WORKSPACE)}"


def _handle_out_flag(args, result):
    """If --out <path> is in args, write result to that file and return a
    confirmation message. Otherwise return result for stdout."""
    out_flag = "--out"
    try:
        idx = args.index(out_flag)
    except ValueError:
        return result
    if idx + 1 >= len(args):
        return "Error: --out requires a file path"
    out_path = args[idx + 1]
    return cmd_write(out_path, result)


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        print("Usage: pdf-tools <info|text|tables|read|ls|cat|write> [args...] [--out <path>]")
        sys.exit(1)

    cmd = args[0]
    cmd_args = args[1:]

    if cmd == "info":
        if len(cmd_args) < 1:
            print("Usage: pdf-tools info <path>")
            sys.exit(1)
        result = cmd_info(cmd_args[0])
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "text":
        if len(cmd_args) < 2:
            print("Usage: pdf-tools text <path> <page> [--out <path>]")
            sys.exit(1)
        result = cmd_text(cmd_args[0], int(cmd_args[1]))
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "tables":
        if len(cmd_args) < 2:
            print("Usage: pdf-tools tables <path> <page> [fmt] [--out <path>]")
            sys.exit(1)
        fmt = cmd_args[2] if len(cmd_args) > 2 and cmd_args[2] != "--out" else "markdown"
        result = cmd_tables(cmd_args[0], int(cmd_args[1]), fmt)
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "read":
        if len(cmd_args) < 1:
            print("Usage: pdf-tools read <path> [--out <path>]")
            sys.exit(1)
        result = cmd_read(cmd_args[0])
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "ls":
        subpath = cmd_args[0] if len(cmd_args) > 0 and cmd_args[0] != "--out" else "."
        result = cmd_ls(subpath)
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "cat":
        if len(cmd_args) < 1:
            print("Usage: pdf-tools cat <path>")
            sys.exit(1)
        result = cmd_cat(cmd_args[0])
        print(_handle_out_flag(cmd_args, result))
    elif cmd == "write":
        if len(cmd_args) < 2:
            print("Usage: pdf-tools write <path> <content>")
            sys.exit(1)
        print(cmd_write(cmd_args[0], " ".join(cmd_args[1:])))
    else:
        print(f"Unknown command: {cmd}")
        print("Available: info, text, tables, read, ls, cat, write")
        sys.exit(1)


if __name__ == "__main__":
    main()
