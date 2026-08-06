---
description: Read, extract text and tables from PDFs, list workspace files, read/write text files via the pdf-tools CLI.
---

# PDF Tools

Use the `pdf-tools` CLI to work with PDF files in the workspace.

## Commands

```bash
pdf-tools read <path>              # full text, all pages
pdf-tools info <path>              # page count
pdf-tools text <path> <page>       # extract text from a single page (1-indexed)
pdf-tools tables <path> <page>     # extract tables as markdown
pdf-tools tables <path> <page> html # extract tables as HTML
pdf-tools ls [subpath]             # list workspace directory
pdf-tools cat <path>               # read a UTF-8 text file
pdf-tools write <path> <content>   # create/overwrite a text file
```

## Paths

All paths are relative to `/workspace` (the mounted workspace directory). You can also use absolute paths like `/workspace/foo.pdf`.

## Example workflow

1. `pdf-tools info report.pdf` — check how many pages
2. `pdf-tools read report.pdf` — read the full document
3. `pdf-tools text report.pdf 3` — extract text from page 3
4. `pdf-tools tables report.pdf 2` — extract tables from page 2

## Important

- The `pdf-tools` command is available via bash — always invoke it through the bash tool.
- For PDFs, prefer `pdf-tools read` and `pdf-tools text` over the built-in `read_file` tool, which cannot parse PDF content.
- Page numbers are 1-indexed (first page is 1).
