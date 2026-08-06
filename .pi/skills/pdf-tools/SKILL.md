---
description: Read, extract text and tables from PDFs, list workspace files, read/write text files via the pdf-tools CLI.
---

# PDF Tools

Use the `pdf-tools` CLI to work with PDF files in the workspace.

## Commands

All file output commands support `--out <path>` to save directly to a file instead of stdout.

```bash
pdf-tools read <path>                           # full text, all pages
pdf-tools read <path> --out /workspace/out.txt  # save to file
pdf-tools info <path>                           # page count
pdf-tools text <path> <page>                    # extract text from a page (1-indexed)
pdf-tools text <path> <page> --out /workspace/p3.txt
pdf-tools tables <path> <page>                  # extract tables as markdown
pdf-tools tables <path> <page> html             # extract tables as HTML
pdf-tools tables <path> <page> html --out /workspace/table.html
pdf-tools ls [subpath]                          # list workspace directory
pdf-tools cat <path>                            # read a UTF-8 text file
pdf-tools write <path> <content>                # create/overwrite a text file
```

## Paths

All paths are relative to `/workspace`. Always use `/workspace/` prefix for file arguments. Example: `pdf-tools read /workspace/report.pdf`

## Example workflow

1. `pdf-tools ls` — see what's in the workspace
2. `pdf-tools info /workspace/report.pdf` — check how many pages
3. `pdf-tools read /workspace/report.pdf` — read the full document
4. `pdf-tools tables /workspace/report.pdf 2 html --out /workspace/table.html` — extract and save table from page 2
5. `pdf-tools write /workspace/summary.md "## Summary\n\n..."` — create a new file
