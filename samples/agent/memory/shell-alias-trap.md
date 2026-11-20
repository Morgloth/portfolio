---
name: shell-alias-trap
description: Never name PowerShell helper functions after built-in aliases (rd = Remove-Item); a "read-only" scan deleted 5 files
metadata:
  type: feedback
---

In PowerShell scripts for a Windows machine, never define functions whose names are built-in aliases: rd, rm, ri,
del, erase, rmdir, cp, copy, mv, move, ren, sc, kill, gc, cat... Aliases win over functions, so
`function rd($f){...}; rd $file` ran Remove-Item and deleted the files.

**Why:** a scan the agent wrote as read-only deleted 5 files; `$ErrorActionPreference='SilentlyContinue'` hid it.

**How to apply:** for read-only scans, call .NET directly ([IO.File]::ReadAllText, [IO.File]::Exists), give helpers
a prefix (Read-SaveText), don't blanket-silence errors on a first run, and check `Get-Alias <name>` when unsure.

Related: [[root-steps]]
