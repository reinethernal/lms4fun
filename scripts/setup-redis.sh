#!/usr/bin/env bash
set -euo pipefail

systemctl enable redis-server
systemctl start redis-server
redis-cli ping
echo "Redis ready on 127.0.0.1:6379"
