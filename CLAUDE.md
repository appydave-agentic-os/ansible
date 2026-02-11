# Ansible macOS Dev Environment

Ansible project that provisions and keeps 3 macOS workstations in sync.

## Machines

| Host            | Hardware         | Connection | Notes                    |
|-----------------|------------------|------------|--------------------------|
| `mac-mini-m2`   | Mac Mini M2 Pro  | local      | Primary dev machine      |
| `mac-mini-m4`   | Mac Mini M4      | SSH        | Second workstation       |
| `macbook-pro-m4`| MacBook Pro M4   | SSH        | Laptop                   |

Owner: David Cruwys (`davidcruwys`), GitHub orgs: `appydave-agentic-os`, `klueless-io`, `AppyDave`

## How to Run

```bash
cd ~/dev/ad/agentic-os/ansible

# Normal run — install missing packages only
ansible-playbook site.yml --limit mac-mini-m2

# Upgrade run — install missing + upgrade everything to latest
ansible-playbook site.yml --limit mac-mini-m2 -e upgrade_packages=true

# Dry run (preview changes)
ansible-playbook site.yml --limit mac-mini-m2 --check --diff

# Single role only
ansible-playbook site.yml --limit mac-mini-m2 --tags homebrew

# All machines at once
ansible-playbook site.yml
```

## Key Architecture

- **`upgrade_packages` toggle** (default: `false`): Controls whether roles install-only (`state: present`) or upgrade (`state: latest`). Pass `-e upgrade_packages=true` when catching up a stale machine.
- **`*_extra` list pattern**: Roles merge base lists with `*_extra` lists (e.g. `homebrew_casks + homebrew_casks_extra`). Host-specific vars in `host_vars/` can add items without overriding the shared base in `group_vars/all.yml`.
- **Secrets handling**: `.zshrc` template sources `~/.secrets` for API keys/tokens. Ansible only creates the empty placeholder with `0600` permissions — never manages secret content.
- **Version managers**: rbenv/nvm/pyenv use `ansible.builtin.shell` with idempotency guards since they're shell functions, not system binaries.
- **Tags**: Every role has a tag (`homebrew`, `applications`, `shell`, `macos`, `languages`, `repos`).

## Project Structure

```
inventory/
  hosts.yml               # 3 Macs: local + 2 remote
  group_vars/all.yml       # All shared config (package lists, versions, defaults)
  host_vars/               # Per-machine overrides
roles/
  homebrew/                # Taps + formulae (state toggles with upgrade_packages)
  applications/            # Cask apps (state toggles with upgrade_packages)
  shell/                   # Oh My Zsh, .zshrc/.zprofile templates, ~/.secrets
  macos_defaults/          # Finder, Dock, keyboard via osx_defaults + handlers
  languages/               # rbenv (ruby.yml), nvm (node.yml), pyenv (python.yml)
  repos/                   # Git config + clone/update repos
```

## Updating Versions

To bump a language version across all machines:
1. Edit `inventory/group_vars/all.yml` — change e.g. `rbenv_ruby_global: "3.5.0"` and add `"3.5.0"` to `rbenv_ruby_versions`
2. Run `ansible-playbook site.yml --limit mac-mini-m2 --tags languages` on each machine
3. The old version stays installed (harmless); the new version gets installed and set as global

To add a new Homebrew package:
1. Add it to `homebrew_formulae` in `group_vars/all.yml` (or `homebrew_formulae_extra` in a host_vars file for machine-specific)
2. Run with `--tags homebrew`

## Common Issues

- **Homebrew macOS version error**: If `brew` doesn't support the macOS version (e.g. macOS 26.x beta), Homebrew modules will fail. Update Homebrew first: `brew update`.
- **Galaxy dependencies**: Run `ansible-galaxy collection install -r requirements.yml` if `community.general` is missing.
- **Remote SSH**: Remote hosts need SSH access configured. Update `ansible_host` in `inventory/hosts.yml` with actual IPs or `.local` hostnames.
