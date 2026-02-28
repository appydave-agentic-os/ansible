# Post-Ansible Setup Checklist

**When to use this**: After running `ansible-playbook site.yml` on a machine.
Ansible handles software installation. This checklist covers everything that requires human interaction.

Work through each section top to bottom. Check items off as you go.

---

## All Machines (do this on every Mac)

### Tailscale Authentication
- [ ] Click Tailscale in the menu bar → Log In
- [ ] Complete browser login
- [ ] Run `tailscale ip` and note the IP address
- [ ] Update `inventory/hosts.yml` with the Tailscale IP for this machine

### SSH Keys
- [ ] Generate SSH key if not already present: `ssh-keygen -t ed25519 -C "david@ideasmen.com.au"`
- [ ] Add public key to GitHub: `cat ~/.ssh/id_ed25519.pub` → GitHub Settings → SSH Keys

### Dotfiles
- [ ] `git clone git@github.com:appydave/dotfiles.git ~/dotfiles`
- [ ] `cd ~/dotfiles && ./install.sh`

### 1Password
- [ ] Sign in to 1Password account
- [ ] Install browser extension in Chrome

---

## Mac Mini M4 (Primary Workstation)

### Audio Routing — MUST DO BEFORE USING ECAMM
*(Prevents Ecamm from hijacking audio away from Wispr Flow and other apps)*

- [ ] Open **Audio MIDI Setup** (Applications → Utilities → Audio MIDI Setup)
- [ ] Click **+** bottom-left → **Create Aggregate Device**
- [ ] Name it: `Streaming Aggregate`
- [ ] Check both boxes:
  - [ ] Your physical mic (HyperX QuadCast or Scarlett interface)
  - [ ] BlackHole 2ch
- [ ] Set **Clock Source** to your physical device (NOT BlackHole)
- [ ] Close Audio MIDI Setup

Then configure apps to use it:
- [ ] **Ecamm Live**: Preferences → Audio → Input → `Streaming Aggregate`
- [ ] **System Settings** → Sound → Input → `Streaming Aggregate` (for Wispr Flow)

### Tailscale (see All Machines above)

### Screen Sharing & Remote Login
*(Should be enabled by Ansible tailscale role — verify)*
- [ ] System Settings → General → Sharing → Screen Sharing ✅
- [ ] System Settings → General → Sharing → Remote Login ✅
- [ ] System Settings → General → Sharing → File Sharing ✅

### Manual Cask Installs (system extensions — require GUI approval)
Run each, then approve in **System Settings → Privacy & Security**:
- [ ] **Tailscale** → Mac App Store: https://apps.apple.com/app/tailscale/id1475387142 (brew cask pkg is unreliable) → log in, run `tailscale ip`
- [ ] **Docker** → download from https://www.docker.com/products/docker-desktop/ (brew cask unreliable) → launch to finish setup
- [ ] **Logi Options+** → download from https://www.logitech.com/en-au/software/logi-options-plus.html → install → approve input monitoring extension (no Homebrew cask available)
- [ ] `brew install --cask ecamm-live` → approve screen capture extension
- [ ] `brew install --cask elgato-stream-deck` → approve system extension

### Manual App Installs (not in Homebrew)
- [ ] **Wispr Flow** — download from wispr.flow, install, configure mic input to `Streaming Aggregate`
- [ ] **DaVinci Resolve** — download from blackmagicdesign.com
- [ ] **Gling.AI** — download from gling.ai

### Licensed Software
- [ ] **Alfred** — enter license key (Preferences → enter license)

### Obsidian
- [ ] Open Obsidian → Create new vault
- [ ] Vault name: `Agentic OS`
- [ ] Location: `~/dev/ad/obsidian-vaults/agentic-os/` (or preferred path)
- [ ] Test Obsidian CLI: `obsidian://open?vault=Agentic%20OS`

### Stream Deck
*(Software installed by Ansible — configure profiles manually)*
- [ ] Open Elgato Stream Deck app
- [ ] Set up profiles for: streaming mode, dev mode, voice control triggers
- [ ] Assign Ecamm scene switching buttons

### Monitor Arrangement (displayplacer)
- [ ] Connect all monitors
- [ ] Arrange monitors in System Settings as desired
- [ ] Capture the config: `displayplacer list`
- [ ] Save the output command to `~/bin/streaming-mode` script (for automation)

### Docker & N8N
- [ ] Start Docker Desktop, ensure it launches on login
- [ ] Install N8N via Docker:
  ```bash
  docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
  ```
- [ ] Open N8N: http://localhost:5678
- [ ] Create admin account

---

## MacBook Pro M4 (Field Machine / Control Node)

### Tailscale (see All Machines above)

### Licensed Software
- [ ] **Alfred** — enter license key

### Ecamm Live
*(Installed by Ansible — verify configuration)*
- [ ] Open Ecamm Live, check audio/video sources are correct for mobile setup

### Stream Deck
*(Installed by Ansible — configure profiles)*
- [ ] Set up profiles for field use (may differ from M4 Mini)

### Ansible SSH Access to Remote Machines
*(Do this once Tailscale IPs are known)*
- [ ] Test SSH to M4 Mini: `ssh davidcruwys@mac-mini-m4.local`
- [ ] Test SSH to M2 Mini: `ssh davidcruwys@mac-mini-m2.local`
- [ ] Run discovery playbook to verify Ansible reaches both: `ansible-playbook discovery.yml`

---

## Mac Mini M2 (Bot Machine)

### Passwordless Sudo (required before tailscale role can run)
The tailscale role uses `become: true` — sudo must be passwordless or Ansible can't run it.

- [ ] Run from your terminal (one-time setup):
  ```bash
  ssh -t davidcruwys@mac-mini-m2.local \
    "echo 'davidcruwys ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/davidcruwys && sudo chmod 440 /etc/sudoers.d/davidcruwys"
  ```
- [ ] Verify: `ssh davidcruwys@mac-mini-m2.local "sudo visudo -c -f /etc/sudoers.d/davidcruwys && echo OK"`
- [ ] Then run: `ansible-playbook site.yml --limit mac-mini-m2 --tags tailscale -v`
- [ ] Optional — remove after provisioning is complete (more secure):
  `ssh davidcruwys@mac-mini-m2.local "sudo rm /etc/sudoers.d/davidcruwys"`
  *(For a headless machine on a private Tailscale network, leaving it on is reasonable)*

### Tailscale (see All Machines above)
*(Critical — this machine is going to the shop. Must be done before it leaves the local network.)*

### Verify Headless Access Before Moving to Shop
- [ ] Test Screen Sharing from MacBook: `vnc://mac-mini-m2.local`
- [ ] Test SSH from MacBook: `ssh davidcruwys@mac-mini-m2.local`
- [ ] Test Screen Sharing via Tailscale IP: `vnc://[tailscale-ip]`
- [ ] Confirm all three work before the machine leaves home network

### Screen Sharing & Remote Login
*(Should be enabled by Ansible tailscale role — verify)*
- [ ] System Settings → General → Sharing → Screen Sharing ✅
- [ ] System Settings → General → Sharing → Remote Login ✅

### Auto-Login (for headless bot operation)
- [ ] System Settings → General → Login Items & Extensions → set automatic login
- [ ] This ensures machine is accessible immediately after a power cycle without physical access

---

## Final Verification (all machines done)

- [ ] `tailscale status` from MacBook shows all 3 machines online
- [ ] Can Screen Share to M4 Mini
- [ ] Can Screen Share to M2 Mini
- [ ] Ansible can reach both remotes: `ansible all -m ping`
- [ ] Audio Aggregate Device working in Ecamm + Wispr Flow simultaneously

---

**Related docs**:
- `inventory/hosts.yml` — update Tailscale IPs here
- Brain: `agentic-os/live-streaming-setup.md` — audio routing detail
- Brain: `agentic-os/machine-to-machine-control.md` — Screen Sharing patterns
- Brain: `agentic-os/setup-roadmap.md` — phase overview
