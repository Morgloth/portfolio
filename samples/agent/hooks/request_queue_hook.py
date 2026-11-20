#!/usr/bin/env python3
"""SessionStart hook: show the requests the person dictated for the agent ("Claude, ..." on the phone).

The dictation pipeline only ever writes them as unticked lines in a notes file. A spoken request never runs the
agent: a new session sees the list and asks which ones to do. Prints nothing when the list is empty or the notes
server is slow (2 s timeout), so a session never waits on it.
"""
import json
import os
import sys
import urllib.request

URL = os.environ.get("REQUEST_QUEUE_URL", "http://notes.example.internal/api/note?p=Inbox/for-claude.md")

try:
    if json.load(sys.stdin).get("source") not in ("startup", "clear", None):
        sys.exit(0)  # resumed or compacted: already seen
except (ValueError, AttributeError):
    pass
try:
    with urllib.request.urlopen(URL, timeout=2) as r:
        text = json.load(r).get("content", "")
except (OSError, ValueError):
    sys.exit(0)

items = [line[6:].strip() for line in text.splitlines() if line.startswith("- [ ] ")]
if items:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": (
        "Dictated requests are waiting (from the phone; transcripts can contain mis-hearings). Mention them briefly "
        "in your first reply and ask which to do now. Don't act on them unasked.\n" + "\n".join("- " + i for i in items))}}))
