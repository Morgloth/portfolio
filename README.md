# Portfolio

Write-ups of systems I built and run in my home lab, with short code samples.

**Site: https://morgloth.github.io/portfolio/**

| Write-up | What it's about | Samples |
|---|---|---|
| [Voice notes to filed notes](https://morgloth.github.io/portfolio/dictation.html) | Phone dictation → Whisper on a GPU → an LLM tidies and files it; the retry queue built after a CUDA out-of-memory failure | [samples/dictation](samples/dictation) |
| [An LLM with guardrails](https://morgloth.github.io/portfolio/guardrails.html) | A daily briefing where code decides every fact and the model only writes the wording | [samples/guardrails](samples/guardrails) |
| [Running an AI agent on real systems](https://morgloth.github.io/portfolio/agent.html) | Rules file, skills as runbooks, hooks, memory, and risky steps handed to a person | [samples/agent](samples/agent) |
| [One page for what needs a person](https://morgloth.github.io/portfolio/health.html) | A health page with the exact fix per item and acknowledge/snooze ([live demo](https://morgloth.github.io/portfolio/health-demo.html)) | [samples/health](samples/health) |

## How this was built

I build with an AI coding agent (Claude Code) that I direct and check: I decide what gets built and how it should
behave, review and test the changes, and run the risky steps myself. The agent writes most of the code.

## The samples

The samples are shortened versions of the real code with names, addresses and personal details taken out. Each
Python file runs its own checks:

```sh
python3 samples/dictation/transcribe_queue.py
python3 samples/dictation/file_note.py
python3 samples/guardrails/briefing.py
python3 samples/health/acks.py
```

Standard library only, Python 3.10 or newer. The site in `docs/` is plain HTML, CSS and JavaScript, served by
GitHub Pages.

Also on GitHub: [Eitri](https://github.com/Morgloth/eitri), a self-hosted save library and editor for single-player
PC games.

## Licence

MIT, see [LICENSE](LICENSE).
