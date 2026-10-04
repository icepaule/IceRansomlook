#!/usr/bin/env python3
"""RansomLook /api/recent -> MISP events (one per post, event uuid = RansomLook misp_uuid).
Targets are read from targets.json: [{"name","url","key_file","verify_tls"}]."""
import json, os, sys, time, datetime, urllib.request, ssl

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")
RECENT = os.environ.get("RL_RECENT", "200")
TAGS = ["ransomware", "tlp:clear", "source:ransomlook"]


def http(url, key=None, data=None, verify=True):
    h = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "ransomlook-misp/1.0"}
    if key:
        h["Authorization"] = key
    ctx = None if verify else ssl._create_unverified_context()
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = None
        return e.code, body


def build_event(p):
    g = p["group_name"]
    day = p["discovered"][:10]
    desc = (p.get("description") or "").strip()[:1500]
    attrs = [
        {"type": "text", "category": "Other", "value": p["post_title"], "comment": "Victim named on leak site", "to_ids": False},
        {"type": "link", "category": "External analysis", "value": f"https://www.ransomlook.io/group/{g}", "comment": "RansomLook group page", "to_ids": False},
    ]
    if desc:
        attrs.append({"type": "comment", "category": "Other", "value": desc, "to_ids": False})
    return {"Event": {
        "uuid": p["misp_uuid"],
        "info": f"RansomLook: {g} - {p['post_title']}"[:250],
        "date": day, "distribution": "0", "threat_level_id": "3", "analysis": "2",
        "Tag": [{"name": t} for t in TAGS + [f"ransomware-group:{g}"]],
        "Attribute": attrs,
    }}


def main():
    targets = json.load(open(os.path.join(BASE, "targets.json")))
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    code, posts = http(f"https://www.ransomlook.io/api/recent/{RECENT}")
    if code != 200 or not isinstance(posts, list):
        print(f"ransomlook fetch failed: {code}", file=sys.stderr); return 1
    posts = [p for p in posts if p.get("misp_uuid") and not p.get("private")]
    rc = 0
    for t in targets:
        seen = set(state.get(t["name"], []))
        key = open(t["key_file"]).read().strip()
        new = ok = 0
        for p in sorted(posts, key=lambda x: x["discovered"]):
            if p["misp_uuid"] in seen:
                continue
            new += 1
            code, body = http(t["url"].rstrip("/") + "/events/add", key, build_event(p), t.get("verify_tls", True))
            err = json.dumps(body)[:300] if body else ""
            if code in (200, 201) or (code in (403, 404, 409, 500) and "already exists" in err.lower()) or "Event already exists" in err:
                seen.add(p["misp_uuid"]); ok += 1
            else:
                print(f"[{t['name']}] FAIL {p['post_title']!r}: {code} {err}", file=sys.stderr); rc = 2
            time.sleep(0.3)
        state[t["name"]] = sorted(seen)[-2000:]
        print(f"[{t['name']}] new={new} created={ok}")
    json.dump(state, open(STATE, "w"))
    return rc


sys.exit(main())
