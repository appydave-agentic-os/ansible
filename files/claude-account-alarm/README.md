# claude-account-alarm

Alarm for the Claude login file on one machine. Checks which account the file-store login belongs to and alerts if it is not the expected one.

- Runs every 15 min via launchd (`com.appydave.claude-file-account-check.plist`).
- Expected email: set `EXPECTED_EMAIL` in the plist. Alerts go to Captain's Log at `http://127.0.0.1:7101` (one capture per episode).
- Looks up the account with Anthropic's `/api/oauth/profile` using the file's token, in-process, never printed. Re-checks on file change and every 24 h.
- Installed location: `~/.local/share/claude-account-alarm/`; status and log in `~/.local/state/claude-account-alarm/`.
- `fixtures/` is fake data only, for testing.
- Not wired into any role or playbook; install is manual (see the comment in the plist).

## Cannot detect

- The Keychain / GUI store
- A running seat's in-memory login
- Env-token sessions
- A flip-and-revert within 15 min
- Expired-token windows

Background: the owner's private notes on Claude's two login stores.
