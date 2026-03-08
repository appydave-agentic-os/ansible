# Bootstrap — New Machine Setup

Run these steps **before** Ansible. This is the "day zero" setup for any machine
that is self-provisioning (i.e. not being remotely provisioned from the control node).

---

## Step 1 — Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Press RETURN when prompted. Enter your password when asked. Takes 2-5 minutes.

After it completes, add Homebrew to your PATH:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Verify:

```bash
brew --version
```

---

## Step 2 — Install Ansible

```bash
brew install ansible
```

Verify:

```bash
ansible --version
```

---

## Step 3 — Clone the Ansible repo

```bash
mkdir -p ~/dev/ad
git clone https://github.com/appydave-agentic-os/ansible.git ~/dev/ad/agent-os/ansible
cd ~/dev/ad/agent-os/ansible
```

---

## Step 4 — Install Ansible requirements

```bash
ansible-galaxy collection install -r requirements.yml
```

---

## Step 5 — Run the playbook

```bash
ansible-playbook site.yml --limit localhost -c local
```

> **Note**: `--limit localhost -c local` runs the playbook against your own machine
> without needing SSH. Use this for self-provisioning.

---

## Who needs this?

- **Client machines** self-provisioning (not being set up remotely by David)
- **New team member machines** before they're added to the Tailscale network

## Who does NOT need this?

- David's machines — provisioned from the MacBook Pro M4 control node via SSH
- Machines already on the Tailscale network reachable from the control node
