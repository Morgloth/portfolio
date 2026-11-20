#!/usr/bin/env python3
"""UserPromptSubmit hook: when the person signs off ("goodnight", "done for the day", "taking a break"), remind the
agent to wrap up before it replies: save what it learned to memory, commit and push, report what's still open.
The note tells the agent to ignore it when the phrase means something else ("set up a goodnight scene")."""
import json
import re
import sys

SIGN_OFF = re.compile(
    r"\b(good\s*night(?!\s+(scene|routine|automation|mode|light|lights))|done for (the )?(day|now)"
    r"|(take|taking) a (short |quick )?break(?!\s+from)|calling it a (day|night)|signing off|going to bed"
    r"|that'?s (it|all) for (today|tonight|now))\b", re.I)

try:
    prompt = json.load(sys.stdin).get("prompt", "")
except (ValueError, AttributeError):
    sys.exit(0)
if not SIGN_OFF.search(prompt):
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": (
            "A sign-off phrase was detected. If the person is really ending the session, wrap up before replying; "
            "if the phrase means something else here, ignore this note.\n"
            "1. Save anything worth remembering to memory, including unfinished work and next steps, with absolute dates.\n"
            "2. Run the wrap-up script (commit + push, memory backup, health check) and fix or report any FAIL.\n"
            "3. Reply briefly: what was saved, what's still open."),
    },
    "systemMessage": "Sign-off detected: the agent will wrap up.",
}))
