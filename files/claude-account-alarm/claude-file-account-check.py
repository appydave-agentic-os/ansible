#!/usr/bin/python3
"""claude-file-account-check — alarm when the M2's Claude FILE login switches account.

PROTOTYPE, not installed. Read-only towards the login: it never writes, refreshes
or rotates ~/.claude/.credentials.json and never prints, logs or stores a token.

Why this signal: the credentials file holds no account or org id in clear (key
names measured 2026-10-12: accessToken, refreshToken, expiresAt,
refreshTokenExpiresAt, scopes, subscriptionType, rateLimitTier). `claude auth
status` and ~/.claude.json show a cached profile shared with GUI sessions. The
only signal that names the account the FILE token belongs to is the same call
Claude Code makes itself: GET /api/oauth/profile with that token (no inference,
no usage cost). The token lives only inside this process's memory and the
HTTPS request header; output is limited to email + account/org uuids.

Refresh vs account change: the file is rewritten on every ~8 h token refresh,
so mtime alone cries wolf. mtime is only the trigger to re-verify; the alarm
fires when the profile's account differs from EXPECTED_EMAIL.

Flow per run (launchd, every 15 min):
  1. stat the file (no read). Same mtime as last verified run and verified
     < 24 h ago -> exit, no network.
  2. read the file in-process. Access token expired -> "pending" (a seat will
     refresh it; nothing bills on an expired token); do NOT refresh it.
  3. GET /api/oauth/profile -> email, account uuid, org uuid.
  4. match -> state ok. mismatch -> one Captain's Log capture per episode
     (idempotent externalId) + status file; repeats only log.

Usage:
  claude-file-account-check.py                      # real run
  claude-file-account-check.py --dry-run            # never posts to CL; prints the alert
  claude-file-account-check.py --creds F --profile-fixture P --state-dir D --dry-run
                                                    # fixture test, no network at all
"""
import argparse
import datetime
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request

PROFILE_URL = "https://api.anthropic.com/api/oauth/profile"
REVERIFY_SECONDS = 24 * 3600
DEFAULT_EXPECTED = "david@ideasmen.com.au"


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def log(event, **fields):
    print(json.dumps(dict(ts=now_iso(), event=event, **fields)), flush=True)


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def fetch_profile(creds_path, fixture_path):
    """Returns (status, identity). identity holds only non-secret fields."""
    try:
        with open(creds_path) as f:
            oauth = json.load(f).get("claudeAiOauth") or {}
    except (OSError, ValueError) as e:
        return "unreadable", {"error": type(e).__name__}
    if not oauth.get("accessToken"):
        return "no-oauth-login", {}
    if (oauth.get("expiresAt") or 0) / 1000 < time.time() + 60:
        return "pending-expired-token", {}

    if fixture_path:
        data = load_json(fixture_path, {})
    else:
        req = urllib.request.Request(PROFILE_URL, headers={
            "Authorization": "Bearer " + oauth["accessToken"],
            "Content-Type": "application/json",
            "User-Agent": "claude-file-account-check/0.1",
        })
        oauth = None  # drop the reference; the token is not needed past this point
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            return "profile-http-error", {"http": e.code}
        except Exception as e:  # never str(e): keep any request detail out of logs
            return "profile-error", {"error": type(e).__name__}
        finally:
            req = None

    account = data.get("account") or {}
    org = data.get("organization") or {}
    email = (account.get("email_address") or account.get("email") or "").lower()
    if not email:
        return "profile-unparsed", {"keys": sorted(data.keys())}
    return "ok", {
        "email": email,
        "account_uuid": account.get("uuid"),
        "org_uuid": org.get("uuid"),
        "org_name": org.get("name"),
    }


def post_capture(cl_url, title, text, external_id, dry_run):
    body = {"title": title, "text": text, "externalId": external_id}
    if dry_run:
        log("alert-dry-run", capture=body)
        return True
    req = urllib.request.Request(cl_url.rstrip("/") + "/api/captures",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:  # CL enriches synchronously, ~15-30 s
            log("alert-posted", http=resp.status, result=json.load(resp).get("data"))
        return True
    except Exception as e:
        log("alert-post-failed", error=type(e).__name__, http=getattr(e, "code", None))
        return False


def main():
    home = os.path.expanduser("~")
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds", default=os.path.join(home, ".claude", ".credentials.json"))
    ap.add_argument("--expected", default=os.environ.get("EXPECTED_EMAIL", DEFAULT_EXPECTED))
    ap.add_argument("--state-dir", default=os.path.join(home, ".local", "state", "claude-account-alarm"))
    ap.add_argument("--cl-url", default=os.environ.get("CL_LOCAL_URL", "http://127.0.0.1:7101"))
    ap.add_argument("--profile-fixture", help="test only: use this JSON instead of calling the API")
    ap.add_argument("--dry-run", action="store_true", help="print the alert instead of posting it")
    ap.add_argument("--force", action="store_true", help="re-verify even if the file is unchanged")
    args = ap.parse_args()

    os.makedirs(args.state_dir, exist_ok=True)
    state_path = os.path.join(args.state_dir, "state.json")
    state = load_json(state_path, {})
    host = socket.gethostname().split(".")[0]

    try:
        mtime = int(os.stat(args.creds).st_mtime)
    except OSError:
        log("no-credentials-file", creds=args.creds)
        return 0

    fresh = time.time() - state.get("verified_at", 0) < REVERIFY_SECONDS
    if not args.force and mtime == state.get("verified_mtime") and fresh:
        log("unchanged", account=state.get("email"), status=state.get("status"))
        return 0

    status, ident = fetch_profile(args.creds, args.profile_fixture)
    if status != "ok":
        # Unverifiable this run: keep the last verdict, retry next run.
        log(status, **ident)
        return 0

    expected = args.expected.lower()
    match = ident["email"] == expected
    verdict = "ok" if match else "account-changed"
    previous = state.get("status")
    state.update(verified_mtime=mtime, verified_at=time.time(), status=verdict,
                 email=ident["email"], account_uuid=ident["account_uuid"],
                 org_uuid=ident["org_uuid"], checked=now_iso())

    if match:
        if previous == "account-changed":
            log("recovered", account=ident["email"])
        state.pop("alerted_episode", None)
        log("ok", account=ident["email"])
    else:
        state.setdefault("episode_start", mtime)
        episode = "%s:%s:%s" % (host, ident["account_uuid"], state["episode_start"])
        log("account-changed", expected=expected, actual=ident["email"], org=ident["org_name"])
        if state.get("alerted_episode") != episode:
            changed_at = datetime.datetime.fromtimestamp(mtime).astimezone().isoformat(timespec="minutes")
            text = (
                "Claude login alarm on %s: the FILE login (~/.claude/.credentials.json, used by "
                "OpenRig seats and anything started with env -i) now belongs to %s, not %s. "
                "File last rewritten %s. Org: %s. Seats started or restarted since then bill %s. "
                "Fix is David-only: run /login as %s over SSH on %s, then restart the seats. "
                "Background: ~/dev/ad/brains/agentic-os/claude-account-two-stores.md"
                % (host, ident["email"], expected, changed_at, ident["org_name"],
                   ident["email"], expected, host)
            )
            if post_capture(args.cl_url, "Claude login alarm: %s file login is %s" % (host, ident["email"]),
                            text, "claude-file-account:" + episode, args.dry_run):
                state["alerted_episode"] = episode
    if match:
        state.pop("episode_start", None)

    save_json(state_path, state)
    save_json(os.path.join(args.state_dir, "status.json"), {
        "host": host, "status": verdict, "expected": expected, "actual": ident["email"],
        "checked": state["checked"],
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
