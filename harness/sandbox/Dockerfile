FROM python:3.11-slim-bookworm

# Set noninteractive mode so apt doesn't try to prompt.
ENV DEBIAN_FRONTEND=noninteractive

# --- System CLIs ---
# Install common utilities the agent may use via bash. We do this in a
# single RUN command to keep the image layer count small and to allow apt's
# cache to be cleaned up in the same layer.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    jq \
    unzip \
    zip \
    less \
    tree \
    ripgrep \
    fd-find \
    sqlite3 \
    openssl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Debian names the fd binary `fdfind` to avoid conflict with an older tool.
# Symlink `fd` -> `fdfind` so the agent (and any script it writes) can use
# the standard name.
RUN ln -s /usr/bin/fdfind /usr/local/bin/fd

# --- Node.js 20 LTS ---
# Install via NodeSource. This is the standard production-grade way to get
# a current Node on a Debian/Ubuntu system — Debian's own nodejs package
# is often several major versions behind.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# --- Working directory ---
# When a bash command runs inside the container, it starts here. This is
# also where the host's workspace bind-mounts (see harness/config.py's
# SANDBOX_WORKSPACE_PATH).
WORKDIR /workspace
