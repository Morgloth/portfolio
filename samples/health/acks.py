"""Acknowledge and snooze for a "needs a person" list (shortened from the health page).

Every check that finds something adds an item: severity (bad / warn / info), area, title, detail, and the exact
command that fixes it. The list is rebuilt from scratch every few minutes, so an acknowledgement has to find "the
same item" again:

- key:  area + title with the numbers taken out, so "UPS battery at 18%" and "at 17%" are one item.
- kind: "ongoing" (a state, like a full disk) or "event" (it happened, like a failed backup run).
        Ongoing items come back after the reminder you picked (1, 3 or 7 days).
        Events stay hidden until they happen again (a new fingerprint, e.g. the failed run's start time).
- Either one comes back at once if it gets worse, with a note saying why it's back.
- An acknowledgement is dropped once its item has been gone for 2 hours (fixed). A shorter gap is just a check
  that didn't run, and dropping the ack then would make an acknowledged item pop up again later.
Run this file for the checks.
"""
import re

SEV = {"bad": 0, "warn": 1, "info": 2}
REMIND = {"1d": 86400, "3d": 3 * 86400, "7d": 7 * 86400}
FORGET_AFTER = 2 * 3600


def item(sev, area, title, detail="", how="", key=None, fp="", event=False):
    return {"sev": sev, "area": area, "title": title, "detail": detail, "how": how,
            "key": key or f"{area}:{re.sub(r'[0-9][0-9.,]*', '#', title)}",
            "fp": str(fp), "kind": "event" if event else "ongoing"}


def acknowledge(acks, it, remind, now):
    acks[it["key"]] = {"fp": it["fp"], "sev": it["sev"], "at": now, "seen": now,
                       "until": None if it["kind"] == "event" else now + REMIND[remind]}


def apply_acks(items, acks, now):
    """Split items into (shown, hidden). Changes acks in place (seen times, forgotten acks)."""
    shown, hidden = [], []
    for it in items:
        a = acks.get(it["key"])
        if not a:
            shown.append(it)
            continue
        a["seen"] = now
        worse = SEV[it["sev"]] < SEV[a["sev"]]
        again = it["fp"] != a["fp"]
        due = a["until"] is not None and now >= a["until"]
        if not (worse or again or due):
            hidden.append(it)
            continue
        shown.append({**it, "ack_note": "Got worse since you acknowledged it" if worse else
                      "Happened again since you acknowledged it" if again else
                      "Reminder: acknowledged, still not fixed"})
    present = {it["key"] for it in items}
    for k in [k for k, a in acks.items() if k not in present and now - a["seen"] > FORGET_AFTER]:
        del acks[k]
    return shown, hidden


if __name__ == "__main__":
    acks, t = {}, 1_000_000
    ups = item("warn", "Power", "UPS battery at 18%")
    acknowledge(acks, ups, "1d", t)
    assert apply_acks([item("warn", "Power", "UPS battery at 17%")], acks, t + 60)[1]        # same item, still hidden
    shown, _ = apply_acks([item("bad", "Power", "UPS battery at 9%")], acks, t + 120)
    assert shown[0]["ack_note"].startswith("Got worse")                                      # worse: back at once
    shown, _ = apply_acks([item("warn", "Power", "UPS battery at 17%")], acks, t + 86400)
    assert shown[0]["ack_note"].startswith("Reminder")                                       # snooze over
    run = item("bad", "Backups", "Last backup failed", fp="02:30", event=True)
    acknowledge(acks, run, "1d", t)
    assert apply_acks([run], acks, t + 7 * 86400)[1]                                          # events don't time out
    shown, _ = apply_acks([item("bad", "Backups", "Last backup failed", fp="02:30 next day", event=True)], acks, t + 8 * 86400)
    assert shown[0]["ack_note"].startswith("Happened again")
    apply_acks([], acks, t + 8 * 86400 + 600)
    assert acks                                                                               # a short gap keeps acks
    apply_acks([], acks, t + 8 * 86400 + FORGET_AFTER + 1200)
    assert not acks                                                                           # gone 2 h: fixed
    print("acks: all checks passed")
