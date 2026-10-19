#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "==> Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
  postgresql postgresql-contrib \
  redis-server \
  python3-venv python3-dev python3-pip \
  libpq-dev build-essential \
  ruby-full ruby-dev \
  nodejs npm \
  default-jdk \
  gcc g++ make pkg-config libcap-dev \
  wget unzip curl openssl \
  git

# Swap (2GB) if not present
if ! swapon --show | grep -q '/swapfile'; then
  echo "==> Creating 2GB swap..."
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

systemctl enable postgresql redis-server
systemctl start postgresql redis-server

echo "==> System packages installed."
