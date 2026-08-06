---
description: Read, extract text and tables from PDFs, list workspace files, read/write text files via the pdf-tools CLI.
---

# PDF Tools

Use the `pdf-tools` CLI to work with PDF files in the workspace.

## Commands

All file output commands support `--out <path>` to save directly to a file instead of stdout.

```bash
pdf-tools read <path>                           # full text, all pages
pdf-tools read <path> --out out.txt         # save to file
pdf-tools info <path>                       # page count
pdf-tools text <path> <page>                # extract text from a page (1-indexed)
pdf-tools text <path> <page> --out p3.txt
pdf-tools tables <path> <page>              # extract tables as markdown
pdf-tools tables <path> <page> html         # extract tables as HTML
pdf-tools tables <path> <page> html --out table.html
pdf-tools ls [subpath]                          # list workspace directory
pdf-tools cat <path>                            # read a UTF-8 text file
pdf-tools write <path> <content>                # create/overwrite a text file
```

## Paths

All file paths are relative to the `files/` directory (`/workspace/files`), where your files live.
Use simple filenames like `report.pdf`.

## Example workflow

1. `pdf-tools ls` — see files in the workspace
2. `pdf-tools info report.pdf` — check how many pages
3. `pdf-tools read report.pdf` — read the full document
4. `pdf-tools tables report.pdf 2 html --out table.html` — extract and save table from page 2
5. `pdf-tools write summary.md "## Summary\n\n..."` — create a new file
