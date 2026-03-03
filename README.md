# Ansible macOS Dev Environment

> Opinionated macOS provisioning for developers who build with AI. Installs a complete development environment across one or more Macs using Ansible and Homebrew.

Built by [AppyDave](https://appydave.com) — part of the [Agentic OS](https://github.com/appydave-agentic-os) project.

---

## What This Does

Runs one command and gets a Mac from factory-fresh to fully configured:

- **Languages**: Ruby (rbenv), Node.js (nvm), Python (pyenv)
- **AI tools**: Claude desktop app, Ollama (local LLMs), Supabase CLI
- **Dev tools**: Git, GitHub CLI, VSCode, iTerm2, Docker (manual), ngrok
- **Shell**: Oh My Zsh with autosuggestions + syntax highlighting
- **Productivity**: Obsidian, Hammerspoon, Zoom, Teams, WhatsApp, Loom
- **Security**: 1Password + 1Password CLI
- **System**: Finder, Dock, keyboard, and display defaults

Works on **Apple Silicon Macs only** (Homebrew at `/opt/homebrew`).

---

## Quick Start

### Prerequisites

1. **Control machine**: The Mac you'll run Ansible from (can be the machine you're provisioning — `localhost` mode)
2. **Ansible**: `pip install ansible` or `brew install ansible`
3. **Galaxy collections**: `ansible-galaxy collection install -r requirements.yml`

### Provision your own Mac (localhost)

```bash
git clone <this-repo>
cd ansible

# 1. Set your identity
cat >> inventory/host_vars/macbook-pro-m4.yml << EOF
git_user_name: Your Name
git_user_email: you@example.com
EOF

# 2. Run it
ansible-playbook site.yml --limit macbook-pro-m4
```

### Provision a remote Mac

```bash
# 1. Copy the client template
cp inventory/host_vars/mac-mini-client-template.yml inventory/host_vars/mac-mini-yourname.yml

# 2. Edit it — set your name and email
# 3. Add your machine to inventory/hosts.yml under remote: and workstation:
# 4. Run it
ansible-playbook site.yml --limit mac-mini-yourname
```

---

## Inventory Structure

Machines are assigned to **functional groups** that control what gets installed:

| Group | What it adds | Machines |
|-------|-------------|---------|
| `all` | Universal base (languages, git, core tools, AI tools) | Every machine |
| `workstation` | GUI apps (Chrome, VSCode, iTerm2, Obsidian, etc.) | Machines with a display |
| `headless` | Minimal install — no GUI apps | Servers, automation nodes |
| `creator` | Video production tools (manual installs only) | Streaming machines |
| `agent` | Automation tooling (future) | Bot machines |
| `david` | AppyDave's personal tools (Ghostty, Alfred, Rectangle, Rust, Postgres) | AppyDave's machines only |
| `client` | Client machine template | CLIENT_USER, future clients |

**The `david` group is AppyDave-specific** — it exists as a reference for what personalisation looks like. Copy this pattern to create your own operator group.

---

## Opinionated Defaults (and How to Change Them)

Every opinion in this playbook is documented so you can adopt, override, or replace it.

### Shell — Oh My Zsh + robbyrussell theme

**Override**: Change `zsh_theme` in `group_vars/all.yml`, edit `zsh_plugins`, or skip the shell role entirely with `--skip-tags shell`.

### Terminal — iTerm2 on workstations

**Why**: Most common macOS developer terminal. AppyDave additionally uses Ghostty (personal preference, `group_vars/david.yml`).
**Override**: Remove `iterm2` from `group_vars/workstation.yml`, add your preferred terminal to `homebrew_casks_extra` in your `host_vars/`.

### Window manager — Rectangle (AppyDave only)

**Why**: Keyboard-driven window snapping. Free.
**Override**: Add `rectangle` to your `host_vars/homebrew_casks_extra`, or use `raycast` (free, includes window management), `magnet` (paid), or macOS native tiling.

### Launcher — Alfred (AppyDave only)

**Why**: Faster than Spotlight, clipboard history, extensible. Requires paid Powerpack for advanced features.
**Override**: Use Spotlight (built-in) or `raycast` (free alternative, add to `homebrew_casks_extra`).

### Rust — AppyDave only

**Why**: AppyDave uses Rust for specific tools. Not installed by default to avoid a heavyweight install for developers who don't need it.
**Override**: Add `rustup` to `homebrew_formulae_extra` in your `host_vars/` and set `rust_toolchain: stable`.

### PostgreSQL 17 vs Supabase CLI

**Two separate things:**

- **Supabase CLI** (`supabase` formula, installed on every machine): Runs a local Supabase stack via Docker. Includes a bundled Postgres, but it's only accessible through the Supabase stack — not as a standalone `psql` target.
- **PostgreSQL 17** (`postgresql@17` formula, AppyDave only): Standalone Homebrew Postgres. Gives you the `psql` client, direct Postgres access, and `libpq` (needed to compile native gems like `pg` for Rails).

**Do you need both?** Only if you're doing Rails development or need direct `psql` access independent of Supabase. If you're building Supabase-native apps, the CLI's bundled Postgres is enough.

**Override**: Add `postgresql@17` to `homebrew_formulae_extra` in your `host_vars/` and set `enable_postgresql_paths: true` to get the `libpq` PATH exports.

### SSH key propagation — disabled by default

**What it does**: When `propagate_ssh_key: true`, copies the control machine's `~/.ssh/id_ed25519` to remote machines (same GitHub identity across all machines).
**Why disabled**: Correct for a single operator with one GitHub account across all their Macs. Wrong for client machines that have their own GitHub accounts.
**Override**: Set `propagate_ssh_key: true` in your operator group vars or specific `host_vars/`.

### macOS defaults

Applied to every machine. The most opinionated:

| Setting | Default | Change in |
|---------|---------|----------|
| Locale | `en_AU` (Australian) | `all.yml` → `AppleLocale` |
| Natural scrolling | Disabled | `all.yml` → `com.apple.swipescrolldirection` |
| Interface | Dark mode | `all.yml` → `AppleInterfaceStyle` |
| Dock | Auto-hide | `all.yml` → `autohide` |

Override individual settings: add `macos_defaults_extra` to `host_vars/` or your group vars.

---

## Adding a New Machine

### Client or team member (workstation)

```bash
# 1. Copy the template
cp inventory/host_vars/mac-mini-client-template.yml inventory/host_vars/mac-mini-yourname.yml

# 2. Edit it
# Set: git_user_name, git_user_email
# Leave: propagate_ssh_key: false (correct for client machines)

# 3. Add to inventory/hosts.yml
# Under remote: → add hostname and ansible_user
# Under workstation: → add the host
# Under client: → uncomment the group and add the host

# 4. Run
ansible-playbook site.yml --limit mac-mini-yourname
```

### After provisioning — manual steps required

Some apps can't be automated because they require macOS system extension approval. See `POST-ANSIBLE.md` for the full checklist. Key manual steps:
- Tailscale → log in via menu bar
- Docker Desktop → download from docker.com, approve system extension
- Creator tools (Ecamm, Stream Deck) → manual install + system extension approval

---

## Running Playbooks

```bash
# Full provision (install missing only)
ansible-playbook site.yml

# Single machine
ansible-playbook site.yml --limit mac-mini-yourname

# Preview changes (dry run)
ansible-playbook site.yml --limit mac-mini-yourname --check --diff

# Upgrade all packages to latest
ansible-playbook site.yml --limit mac-mini-yourname -e upgrade_packages=true

# Single role only
ansible-playbook site.yml --limit mac-mini-yourname --tags homebrew
ansible-playbook site.yml --limit mac-mini-yourname --tags languages
ansible-playbook site.yml --limit mac-mini-yourname --tags shell

# Query current state (read-only, no changes)
ansible-playbook discovery.yml --limit mac-mini-yourname
```

---

## What's Not Covered

- **Tailscale auth** — install is automated, but login requires clicking through the UI once per machine
- **Docker Desktop** — system extension, must be downloaded and installed manually
- **App Store apps** — not automatable
- **Creator tools** — Ecamm Live, Elgato Stream Deck, Gling, DaVinci Resolve are manual installs (system extensions)
- **Dotfiles** — personal config files (`.gitconfig`, Hammerspoon `init.lua`) are managed separately
- **Secrets / API keys** — Ansible creates `~/.secrets` as an empty placeholder with `0600` permissions. You populate it.
- **Intel Macs / Windows / Linux** — Apple Silicon only

---

## Known Issues

**Homebrew macOS version error**: If your macOS is very new (beta) and Homebrew doesn't support it yet, Homebrew modules will fail. Fix: `brew update` first.

**Galaxy collection missing**: Run `ansible-galaxy collection install -r requirements.yml` if you see `community.general not found`.

**SSH connection refused**: Remote hosts need SSH enabled. The `tailscale` role enables Remote Login (`systemsetup -setremotelogin on`) — run the playbook with a direct connection first, then Tailscale takes over.

**NVM not found in SSH sessions**: The `.zshenv` file must load Homebrew. If you provisioned an older machine, re-run the `shell` role: `ansible-playbook site.yml --limit <host> --tags shell`.

---

## Project Layout

```
inventory/
  hosts.yml                 # All machines — add yours here
  group_vars/
    all.yml                 # Universal base — installed on everything
    workstation.yml         # GUI apps for machines with a display
    headless.yml            # Minimal — servers and automation nodes
    creator.yml             # Video production (manual installs only)
    agent.yml               # Automation tooling (future)
    david.yml               # AppyDave personal preferences (reference/template)
  host_vars/
    mac-mini-client-template.yml  # Copy this for each new client/team machine
    macbook-pro-m4.yml
    mac-mini-m4.yml
    mac-mini-m2.yml
roles/
  homebrew/        # Taps + formulae
  applications/    # Cask (GUI) apps
  shell/           # Oh My Zsh, shell config templates
  macos_defaults/  # System preferences
  dock/            # Dock items
  languages/       # rbenv, nvm, pyenv, rustup
  repos/           # Git identity, SSH keys, repo cloning
  tailscale/       # Remote access (SSH, VNC, SMB)
site.yml           # Main playbook
discovery.yml      # Read-only system audit
POST-ANSIBLE.md    # Manual steps after provisioning
CLAUDE.md          # Agent context (preparation pattern format)
```

---

## License

MIT — use it, fork it, adapt it for your own machines.

---

*Part of the [Agentic OS](https://github.com/appydave-agentic-os) project by [AppyDave](https://appydave.com)*
