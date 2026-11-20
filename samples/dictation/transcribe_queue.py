"""Save first, transcribe later: the retry queue from the dictation pipeline (shortened).

A phone recording is written to disk before anything else happens. Then the web app asks the speech-to-text server
(Whisper behind an OpenAI-compatible API) for a transcript. How it reacts depends on *why* a try failed:

  server unreachable (GPU box off or away)  -> stay queued, don't count it; the next timer run tries again
  5xx (the server's own trouble: GPU out     -> stay queued, wait 1, 2, 5, 10, 20, 30 min between tries,
       of memory, model still loading)          give up (and push a notification) only after 2 days
  4xx (it rejects this audio)                -> count it; give up after 3 tries

One GPU means one transcription at a time, so a lock serialises them, and a busy server makes the rest of the
queue wait instead of hammering it. Run this file to see the queue handle each case with a fake server.
"""
import json
import threading
import time
import urllib.error
import urllib.request

BACKOFF_MIN = (1, 2, 5, 10, 20, 30)
GIVE_UP_S = 2 * 86400
MAX_REJECTS = 3
_gpu = threading.Lock()


def whisper(url, audio, mime):
    """POST the audio to /v1/audio/transcriptions and return the text (simplified: the real one builds multipart)."""
    req = urllib.request.Request(url + "/v1/audio/transcriptions", data=audio, method="POST",
                                 headers={"Content-Type": mime})
    with urllib.request.urlopen(req, timeout=180) as r:  # the first call after idle also loads the model
        return (json.load(r).get("text") or "").strip()


def try_once(rec, transcribe, now):
    """One attempt. Changes rec in place and returns True when it's finished (transcribed, or given up on)."""
    try:
        text = transcribe(rec)
    except urllib.error.HTTPError as e:
        rec["error"] = f"server said {e.code}"
        if e.code >= 500:                       # its trouble, not the recording's: queue it, back off
            n = rec.get("busy", 0)
            rec["busy"] = n + 1
            rec["next_try"] = now + 60 * BACKOFF_MIN[min(n, len(BACKOFF_MIN) - 1)]
            if now - rec["created"] > GIVE_UP_S:
                rec["status"] = "error"         # the real code also pushes a phone notification here
            return rec["status"] == "error"
        rec["rejects"] = rec.get("rejects", 0) + 1
        if rec["rejects"] >= MAX_REJECTS:
            rec["status"] = "error"
        return rec["status"] == "error"
    except OSError as e:                        # unreachable: no count, no backoff, just try at the next run
        rec["error"] = f"not reachable ({e})"
        return False
    rec.update(status="raw" if text else "empty", raw=text, error=None)
    return True


def retry_due(queue, transcribe, now):
    """Timer entry point: oldest first, stop as soon as the server says it's busy."""
    with _gpu:
        for rec in sorted(queue, key=lambda r: r["created"]):
            if rec["status"] != "audio" or rec.get("next_try", 0) > now:
                continue
            if not try_once(rec, transcribe, now) and rec.get("next_try", 0) > now:
                break                            # busy: the rest wait too


if __name__ == "__main__":
    def fake(code=None, exc=None, text="Buy milk."):
        def call(rec):
            if code:
                raise urllib.error.HTTPError("http://gpu", code, "x", {}, None)
            if exc:
                raise exc
            return text
        return call

    t = time.time()
    rec = {"created": t, "status": "audio"}
    try_once(rec, fake(code=500), t)
    assert rec["status"] == "audio" and rec["next_try"] == t + 60, rec    # out of memory: wait a minute
    try_once(rec, fake(code=500), t)
    assert rec["next_try"] == t + 120                                      # then two
    try_once(rec, fake(exc=OSError("no route to host")), t)
    assert rec["status"] == "audio" and "rejects" not in rec               # box off: not held against it
    try_once(rec, fake(), t)
    assert rec["status"] == "raw" and rec["raw"] == "Buy milk."
    bad = {"created": t, "status": "audio"}
    for _ in range(MAX_REJECTS):
        try_once(bad, fake(code=400), t)
    assert bad["status"] == "error"
    old = {"created": t - GIVE_UP_S - 1, "status": "audio"}
    try_once(old, fake(code=503), t)
    assert old["status"] == "error"
    q = [{"created": t - 9, "status": "audio"}, {"created": t - 5, "status": "audio"}]
    retry_due(q, fake(code=500), t)
    assert "next_try" in q[0] and "next_try" not in q[1]                   # busy: the second one wasn't tried
    print("transcribe_queue: all checks passed")
