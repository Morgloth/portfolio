---
name: deploy
description: Deploy changed files from this repo to the live machine they mirror, with pull-first, lint, backup, apply and verify. Use whenever repo files need to go live or when the person runs /deploy.
argument-hint: "[repo paths, or nothing = everything changed]"
---

# Deploy

Files to deploy: $ARGUMENTS (if none were given, use the uncommitted changes from `git status --short hosts/`).

The live file is the source of truth: deploying means making live match the repo, and the next hourly sync confirms it.

## 1. Pull first
`git pull --rebase` (stash if the tree is dirty). If the pull changed a file you're about to deploy, re-check your edit.

## 2. Map repo path to target
| Repo prefix | SSH target | Live path |
|---|---|---|
| `hosts/web/app/` | `root@web` | `/srv/app/` |
| `hosts/web/etc/` | `root@web` | `/etc/` |
| `hosts/<other>/` | `root@<other>` | `/` + rest |

**Never deploy:** files whose secrets are redacted in git. Change those on the machine.

## 3. Check
- Python `ruff check`, shell `shellcheck`, JS `node --check`. Fix everything it reports.

## 4. Back up, copy, apply
1. `ssh root@<target> 'tar czf /root/bak-before-<change>.tgz -C / <live paths>'`
2. `scp <repo file> root@<target>:<live path>`, then fix ownership.
3. Apply: restart the unit for code changes, `nginx -t && systemctl reload nginx` for web server config,
   `systemctl daemon-reload` for units.
If the permission mode blocks a root step, don't retry it: hand the person one copyable block, then verify read-only.

## 5. Verify
- The page or API answers 200, the unit is active, the last log lines have no tracebacks.
- If it's broken: restore the backup, re-apply, and tell the person what happened.
