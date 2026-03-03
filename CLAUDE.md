# Ansible macOS Dev Environment — Agent Context

**Pattern**: Preparation Pattern (see ~/dev/ad/brains/prompt-patterns/preparation-pattern.md)
This document packages the knowledge needed for any agent or operator to understand, adapt, and run this playbook on their own machines.

**Source**: This playbook (~/dev/ad/agent-os/ansible/)
**Target**: Any agent, operator, or client receiving this playbook to provision a Mac development environment
**Scope**: macOS multi-machine provisioning — software, shell config, language runtimes, git, system defaults
**Last Updated**: 2026-03-03

---

## Mental Model

This is an **opinionated macOS provisioning system** for developers who use Claude Code as their primary AI tool. It manages multiple Macs consistently via SSH and Homebrew, with a layered group system that separates universal defaults from operator-specific preferences.

**Three-layer architecture:**
```
group_vars/all.yml          — universal baseline (any developer on any Mac)
group_vars/<group>.yml      — role or operator defaults (workstation, creator, david, client)
host_vars/<hostname>.yml    — machine-specific overrides (git identity, extras, flags)
```

**Principle:** A client or new operator should only need to touch `host_vars/` and their group vars. The `all.yml` baseline should run cleanly on any Mac without modification.

**What it installs on every machine:**
- Language runtimes: Ruby (rbenv), Node (nvm), Python (pyenv)
- Core CLI tools: git, gh, ffmpeg, fzf, rsync, tmux, uv, sqlite
- AI tooling: Claude desktop app, Supabase CLI, Ollama
- Shell: Oh My Zsh with zsh-autosuggestions + zsh-syntax-highlighting
- Apps: 1Password, Chrome, VSCode, Zoom, Teams, WhatsApp, Obsidian, Hammerspoon, Loom, ngrok

---

## Required Configuration (Template Parameters)

**These must be set before running — there are no safe defaults.**

| Variable | Where to set | Example |
|----------|-------------|---------|
| `git_user_name` | `host_vars/<hostname>.yml` or `group_vars/<operator>.yml` | `Joe Blow` |
| `git_user_email` | `host_vars/<hostname>.yml` or `group_vars/<operator>.yml` | `joe@example.com` |
| `ansible_user` | `inventory/hosts.yml` under the `remote:` host entry | `joe` |
| `ansible_host` | `inventory/hosts.yml` under the `remote:` host entry | `mac-mini-joe.local` or Tailscale hostname |

**Defaults in `all.yml`:**
- `git_user_name: ""` — empty string skips git config (guarded in task)
- `git_user_email: ""` — empty string skips git config (guarded in task)
- `ansible_user: "{{ lookup('env', 'USER') }}"` — resolves to whoever runs the playbook

---

## Opinionated Defaults

Each decision below was made for a specific reason. Every opinion includes:
- **What it does**
- **Why it was chosen**
- **How to override it** — so an agent or operator can make their own informed decision

---

### OPINION: Shell framework — Oh My Zsh

**What it does**: Installs Oh My Zsh with the `robbyrussell` theme and two plugins: `zsh-autosuggestions` and `zsh-syntax-highlighting`.

**Why chosen**: Widely used, good plugin ecosystem, theme is unobtrusive and informative. The two plugins are near-universally useful (completion prediction + error highlighting).

**How to override**:
- Theme: change `zsh_theme` in `group_vars/all.yml` or your `host_vars/`
- Plugins: edit `zsh_plugins` list in `group_vars/all.yml`
- Remove Oh My Zsh entirely: skip the role with `--skip-tags shell`; replace `.zshrc.j2` with your own template

---

### OPINION: Terminal — iTerm2 (workstation default), Ghostty (David only)

**What it does**: Every workstation gets iTerm2. David's machines additionally get Ghostty (via `group_vars/david.yml`).

**Why chosen**: iTerm2 is the de facto macOS developer terminal — stable, well-known. Ghostty is a newer, faster terminal chosen by David (see ADR-0003 in ~/dev/ad/brains/agentic-os/decisions/).

**How to override**:
- Remove iTerm2: remove from `homebrew_casks_workstation` in `group_vars/workstation.yml`
- Add a different terminal: add to `homebrew_casks_extra` in your `host_vars/`
- Use Ghostty universally: move it from `group_vars/david.yml` to `group_vars/workstation.yml`

---

### OPINION: Window management — Rectangle (David only)

**What it does**: Rectangle is installed on David's machines via `group_vars/david.yml`. Keyboard-driven window snapping.

**Why chosen**: Lightweight, free, keyboard-shortcut-based window management.

**How to override**: Add to `homebrew_casks_extra` in your `host_vars/` for any machine.
Alternatives: `magnet` (paid, App Store), `yabai` (tiling WM, more complex), macOS native tiling (built-in).

---

### OPINION: Launcher — Alfred (David only)

**What it does**: Alfred is installed on David's machines via `group_vars/david.yml`. Requires a paid Powerpack license for advanced features.

**Why chosen**: Faster than Spotlight, extensible workflows, clipboard history.

**How to override**: Use Spotlight (built-in, free). Or add to `homebrew_casks_extra`.
Alternative: `raycast` (free, similar feature set, no license needed).

---

### OPINION: Rust toolchain (David only)

**What it does**: Installs `rustup` and the `stable` toolchain on David's machines via `group_vars/david.yml`. Not installed by default.

**Why chosen**: David uses Rust for specific tools. Excluded from universal baseline — heavyweight with no benefit for Ruby/Python/JS-focused developers.

**How to override**: Add `rustup` to `homebrew_formulae_extra` in your `host_vars/` and set `rust_toolchain: stable`.

---

### OPINION: PostgreSQL 17 (David only) vs Supabase CLI (universal)

**Two separate things — do not confuse them:**

- **`supabase` formula** (universal — `all.yml`): The Supabase CLI. Runs a local Supabase stack (auth, storage, edge functions) via Docker. Bundles its own Postgres instance accessible only through Docker/Supabase stack.
- **`postgresql@17` formula** (David-only — `group_vars/david.yml`): Standalone Homebrew Postgres. Installs the `psql` client, a directly-addressable Postgres server, and `libpq` (needed to compile native gems like the `pg` Ruby gem or `psycopg2`).

**Why split**: You can use Supabase CLI without postgresql@17. But if you use Rails/ActiveRecord, need `psql` as a standalone tool, or need to compile native Postgres extensions, you need postgresql@17. The Supabase CLI's Postgres cannot serve as a standalone `psql` target for external tools.

**How to override**:
- Need direct Postgres access: add `postgresql@17` to `homebrew_formulae_extra` in your `host_vars/`; set `enable_postgresql_paths: true` to get libpq PATH exports in `.zshrc`
- Don't need Supabase at all: remove `supabase` from `homebrew_formulae` in `all.yml`

---

### OPINION: SSH key propagation — disabled by default

**What it does**: When `propagate_ssh_key: true`, the repos role copies the control node's `~/.ssh/id_ed25519` (private + public) to each remote machine.

**Why enabled for David**: Single GitHub identity across all three machines — one SSH key, all machines push/pull as the same account.

**Why disabled by default**: Clients and team members have their own GitHub accounts. Copying the operator's key to a client machine is wrong. `propagate_ssh_key: false` is the safe default in `all.yml`.

**How to override**: Set `propagate_ssh_key: true` in `host_vars/<hostname>.yml` or your operator group vars.

---

### OPINION: macOS system defaults

**What it does**: Sets ~20 Finder, Dock, and input defaults applied to every machine.

**Most opinionated settings:**

| Setting | Default value | Variable to change |
|---------|--------------|-------------------|
| Locale | `en_AU` (Australian English) | `AppleLocale` in `all.yml` |
| Natural scrolling | Disabled (`false`) | `com.apple.swipescrolldirection` |
| Interface | Dark mode | `AppleInterfaceStyle` |
| Dock | Auto-hide | `autohide` |
| Key repeat | Fast (2) | `KeyRepeat` |

**How to override**: Add `macos_defaults_extra` entries in `host_vars/` to override individual keys, or edit `macos_defaults` in `all.yml` directly.

---

### OPINION: Display arrangement — displayplacer (David only)

**What it does**: `displayplacer` is a CLI for programmatic display arrangement. Installed on David's machines via `group_vars/david.yml`.

**Why chosen**: David uses three monitors with specific streaming + dev layouts that need scripted positioning.

**How to override**: Only useful with multiple monitors. Add to `homebrew_formulae_extra` in your `host_vars/` if needed.

---

## Non-Obvious Constraints

**System extension casks must be installed manually.**
These will hang indefinitely if run via Ansible headlessly: `ecamm-live`, `elgato-stream-deck`, `docker`, `tailscale`. Install manually after running the playbook. See `POST-ANSIBLE.md`.

**PATH is not available in shell tasks on remote SSH connections.**
Ansible runs shell tasks with a minimal PATH. The `site.yml` playbook sets PATH via `environment:` at the play level. Always use absolute binary paths or export PATH explicitly in shell tasks.

**`--check` mode lies on fresh machines.**
Dry-run mode cannot verify what would change on a machine without packages installed. Use `--check` for sanity-checking existing machines only.

**NVM is installed via Homebrew, not `~/.nvm`.**
NVM lives at `/opt/homebrew/opt/nvm/nvm.sh`. If `nvm: command not found` appears in SSH sessions, `.zshenv` is likely not loading Homebrew.

**The `~/.secrets` file is never managed content.**
Ansible creates an empty placeholder with `0600` permissions. You populate it with API keys manually. Never commit secrets to this repo.

---

## Scope Limits

This playbook does NOT cover:
- **Tailscale authentication** — installed but requires manual login via the menu bar
- **Docker Desktop** — system extension, manual install required
- **App Store apps** — not automatable via this playbook
- **Creator tools** — Ecamm Live, Stream Deck, Gling, DaVinci Resolve are manual installs
- **Dotfiles** — managed separately via `git@github.com:appydave/dotfiles`
- **Secrets / API keys** — `~/.secrets` placeholder only
- **Windows / Linux** — macOS Apple Silicon only

See `POST-ANSIBLE.md` for the full post-provisioning checklist.

---

## Communication Protocol (for agents)

```
"Add <package> to every machine"
→ Add to homebrew_formulae or homebrew_casks in group_vars/all.yml

"Add <package> to workstations only"
→ Add to homebrew_formulae_workstation or homebrew_casks_workstation in group_vars/workstation.yml

"Add <package> to David's machines only"
→ Add to homebrew_formulae_david or homebrew_casks_david in group_vars/david.yml

"Add a new client machine"
→ 1. Copy host_vars/mac-mini-client-template.yml → host_vars/mac-mini-<name>.yml
  2. Set git_user_name, git_user_email in the new file
  3. Add host entry under remote: in hosts.yml with ansible_host and ansible_user
  4. Add to workstation: and client: groups in hosts.yml

"Change a language version"
→ Edit rbenv_ruby_versions/nvm_node_versions/pyenv_python_versions in group_vars/all.yml
  Then: ansible-playbook site.yml --limit <host> --tags languages

"Run against one machine"
→ ansible-playbook site.yml --limit <hostname>

"Dry run (preview changes)"
→ ansible-playbook site.yml --limit <hostname> --check --diff
```

---

## Project Structure

```
inventory/
  hosts.yml                      # Machine inventory — add your machines here
  group_vars/
    all.yml                      # Universal baseline — every machine
    workstation.yml              # Machines with display/keyboard
    headless.yml                 # No display, minimal footprint
    creator.yml                  # Video production (manual installs only)
    agent.yml                    # Automation nodes
    david.yml                    # David-specific tools + identity
  host_vars/
    mac-mini-client-template.yml # Starting point for client/team machines
    macbook-pro-m4.yml
    mac-mini-m4.yml
    mac-mini-m2.yml
roles/
  homebrew/        # Taps + formulae — merges all group lists
  applications/    # Cask apps — merges all group lists
  shell/           # Oh My Zsh, .zshrc/.zprofile/.zshenv templates
  macos_defaults/  # Finder, Dock, keyboard via defaults write
  dock/            # Dock item management via dockutil
  languages/       # rbenv, nvm, pyenv, rustup (conditional)
  repos/           # Git config, SSH key propagation, repo cloning
  tailscale/       # Enable SSH/VNC/SMB on remote machines
site.yml           # Main playbook — runs all roles against all hosts
discovery.yml      # Read-only — queries current state of a machine
POST-ANSIBLE.md    # Manual steps required after running site.yml
```

---

## Brain References (for agents with access to the brains repo)

| Brain file | What it covers |
|-----------|---------------|
| ~/dev/ad/brains/agentic-os/hardware-infrastructure.md | Machine specs, roles, network topology |
| ~/dev/ad/brains/agentic-os/development-environment.md | Language versions, tool philosophy |
| ~/dev/ad/brains/ansible/INDEX.md | Ansible patterns, safety, macOS lessons |
| ~/dev/ad/brains/ansible/macos-provisioning-lessons.md | Hard-won macOS-specific lessons |
| ~/dev/ad/brains/agentic-os/decisions/README.md | ADR index — all architectural decisions |
