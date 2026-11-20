// Health page demo: made-up items, the same acknowledgement rules as samples/health/acks.py.
"use strict";
(function () {
  var SEV = { bad: 0, warn: 1, info: 2 };
  var REMIND = { "1d": 86400, "3d": 3 * 86400, "7d": 7 * 86400 };
  var FORGET_AFTER = 2 * 3600;
  var START = Date.UTC(2026, 10, 19, 8, 0) / 1000;  // shown as local wall time below, so it's 08:00 for everyone
  var st, acks;

  function reset() {
    st = { now: START, ups: 18, backupRun: "02:30", backupDay: 19, scrubFixed: false, rebootDays: 4 };
    acks = {};
  }

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function fmt(ts) {
    var d = new Date(ts * 1000);
    var mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getUTCMonth()];
    return pad(d.getUTCDate()) + " " + mon + " " + pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes());
  }

  function item(sev, area, title, o) {
    o = o || {};
    return { sev: sev, area: area, title: title, detail: o.detail || "", how: o.how || "",
             key: area + ":" + title.replace(/[0-9][0-9.,]*/g, "#"), fp: o.fp || "", kind: o.event ? "event" : "ongoing" };
  }

  // The "checks": rebuilt from the simulated state on every render, like the real list.
  function checks() {
    var out = [];
    out.push(item("bad", "Backups", "Last nightly backup failed", {
      detail: "web-1, " + pad(st.backupDay) + " Nov " + st.backupRun + ": the datastore is full.",
      how: "ssh backup-host proxmox-backup-manager garbage-collection start store1",
      fp: st.backupDay + " " + st.backupRun, event: true }));
    out.push(item(st.ups < 10 ? "bad" : "warn", "Power", "UPS battery at " + st.ups + "%", {
      detail: st.ups < 10 ? "Runtime under 2 min. A power cut now would hard-stop the hosts." :
        "Runtime 6 min at the current load. The battery is 4 years old.",
      how: "upsc ups@localhost battery.charge" }));
    var r = st.rebootDays;
    out.push(item(r >= 7 ? "bad" : r >= 3 ? "warn" : "info", "Updates", "Host waiting " + r + " days to reboot", {
      detail: "A new kernel is installed. Warning from day 3, red from day 7, and on day 10 it reboots itself at 01:00.",
      how: "ssh host-1 reboot" }));
    if (!st.scrubFixed) {
      out.push(item("warn", "Disks", "Pool scrub 3 days overdue", {
        detail: "The monthly scrub didn't start. No errors on the last one.", how: "ssh host-1 zpool scrub tank" }));
    }
    out.push(item("info", "Certificates", "TLS certificate renews in 21 days", { detail: "Renewal is automatic; this is here in case it isn't." }));
    out.push(item("info", "Monitoring", "CVE watch: 2 new low-severity matches", { detail: "Both in packages with no network exposure." }));
    return out;
  }

  function applyAcks(items) {
    var shown = [], hidden = [], present = {};
    items.forEach(function (it) {
      present[it.key] = true;
      var a = acks[it.key];
      if (!a) { shown.push(it); return; }
      a.seen = st.now;
      var worse = SEV[it.sev] < SEV[a.sev], again = it.fp !== a.fp, due = a.until !== null && st.now >= a.until;
      if (!(worse || again || due)) { hidden.push(Object.assign({}, it, { ack: a })); return; }
      shown.push(Object.assign({}, it, { note: (worse ? "Got worse since you acknowledged it" :
        again ? "Happened again since you acknowledged it" : "Reminder: acknowledged, still not fixed") + " (" + fmt(a.at) + ")" }));
    });
    Object.keys(acks).forEach(function (k) {
      if (!present[k] && st.now - acks[k].seen > FORGET_AFTER) {
        delete acks[k];
        say("The scrub item has been gone for 2 hours, so its acknowledgement was dropped: it's fixed.");
      }
    });
    return [shown, hidden];
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function btn(label, fn) { var b = el("button", "", label); b.type = "button"; b.addEventListener("click", fn); return b; }

  var toastTimer;
  function toast(msg) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("on"); }, 1600);
  }
  function say(msg) { document.getElementById("log").textContent = msg; }

  function ack(it, remind) {
    acks[it.key] = { fp: it.fp, sev: it.sev, at: st.now, seen: st.now, title: it.title, kind: it.kind,
                     until: it.kind === "event" ? null : st.now + REMIND[remind] };
    render();
  }

  function render() {
    var split = applyAcks(checks()), shown = split[0], hidden = split[1];
    shown.sort(function (a, b) { return SEV[a.sev] - SEV[b.sev]; });
    var clock = document.getElementById("clock");
    clock.textContent = "";
    clock.appendChild(document.createTextNode(fmt(st.now) + " "));
    clock.appendChild(el("span", "", "(simulated)"));

    var n = { bad: 0, warn: 0, info: 0 };
    shown.forEach(function (i) { n[i.sev]++; });
    var sum = document.getElementById("summary");
    sum.textContent = "";
    sum.appendChild(el("span", "pill bad", n.bad + " need you now"));
    sum.appendChild(el("span", "pill warn", n.warn + " soon"));
    sum.appendChild(el("span", "pill", n.info + " FYI"));

    var ul = document.getElementById("items");
    ul.textContent = "";
    if (!shown.length) ul.appendChild(el("li", "empty", "Nothing needs you."));
    shown.forEach(function (it) {
      var li = el("li", "item " + it.sev), top = el("div", "top");
      top.appendChild(el("span", "area", it.area));
      top.appendChild(el("span", "title", it.title));
      li.appendChild(top);
      if (it.detail) li.appendChild(el("p", "detail", it.detail));
      if (it.note) li.appendChild(el("p", "note", it.note));
      if (it.how) {
        var how = el("div", "how");
        how.appendChild(el("code", "", it.how));
        how.appendChild(btn("Copy", function () {
          var done = function () { toast("Copied"); };
          if (navigator.clipboard) navigator.clipboard.writeText(it.how).then(done, done); else done();
        }));
        li.appendChild(how);
      }
      var acts = el("div", "acts");
      if (it.kind === "event") {
        acts.appendChild(btn("Acknowledge until it happens again", function () { ack(it); }));
      } else {
        acts.appendChild(el("span", "k", "Acknowledge, remind me in"));
        ["1d", "3d", "7d"].forEach(function (r) { acts.appendChild(btn(r, function () { ack(it, r); })); });
      }
      li.appendChild(acts);
      ul.appendChild(li);
    });

    var det = document.getElementById("acked");
    det.hidden = !hidden.length;
    det.querySelector("summary").textContent = "Acknowledged (" + hidden.length + ")";
    var al = det.querySelector("ul");
    al.textContent = "";
    hidden.forEach(function (it) {
      var li = el("li"), left = el("div");
      left.appendChild(document.createTextNode(it.area + ": " + it.title + " "));
      left.appendChild(el("span", "m", it.ack.until === null ? "until it happens again" : "reminder " + fmt(it.ack.until)));
      li.appendChild(left);
      li.appendChild(btn("Undo", function () { delete acks[it.key]; render(); }));
      al.appendChild(li);
    });
  }

  var sims = {
    hour: function () { st.now += 2 * 3600; say("Two hours later."); },
    day: function () {
      st.now += 86400; st.rebootDays += 1;
      say("A day later. The reboot item climbs its ladder; snoozes that ran out come back as reminders.");
    },
    ups: function () {
      st.ups = Math.max(5, st.ups - 9);
      say("The battery dropped. Same key (numbers don't count), so an acknowledgement still matches, but a worse severity brings it back at once.");
    },
    backup: function () {
      st.backupDay += 1;
      st.now = Math.max(st.now, Date.UTC(2026, 10, st.backupDay, 2, 45) / 1000);
      say("Another nightly run failed: a new fingerprint, so an acknowledged event comes back.");
    },
    scrub: function () {
      st.scrubFixed = true;
      say("Scrub started, so the item is gone. If it was acknowledged, the acknowledgement waits 2 hours before it's dropped, in case this was a gap in the data.");
    }
  };

  document.querySelectorAll("[data-sim]").forEach(function (b) {
    b.addEventListener("click", function () { sims[b.getAttribute("data-sim")](); render(); });
  });
  document.getElementById("reset").addEventListener("click", function () { reset(); say(""); render(); });
  reset();
  render();
})();
