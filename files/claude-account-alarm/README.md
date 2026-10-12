# claude-account-alarm

Alarm for the Claude login file on the **M2 only**. Checks which account the file-store login belongs to and alerts if it is not the expected one.

- Runs every 15 min via launchd (`com.appydave.claude-file-account-check.plist`).
- Expected email: `david@ideasmen.com.au`. Alerts go to Captain's Log at `http://127.0.0.1:7101` (one capture per episode).
- Looks up the account with Anthropic's `/api/oauth/profile` using the file's token, in-process, never printed. Re-checks on file change and every 24 h.
- Installed location on the M2: `~/.local/share/claude-account-alarm/`; status and log in `~/.local/state/claude-account-alarm/`.
- `fixtures/` is fake data only, for testing.
- Not wired into any role or playbook; install is manual (see the comment in the plist).

## Cannot detect

- The Keychain / GUI store
- A running seat's in-memory login
- Env-token sessions
- A flip-and-revert within 15 min
- Expired-token windows

Background: `/Users/davidcruwys/dev/ad/brains/agentic-os/claude-account-two-stores.md`
