#!/usr/bin/env bash
set -euo pipefail

# Symlinks for Judge0 language runtimes (Docker image paths -> host binaries)
mkdir -p /usr/local/python-3.8.1/bin
mkdir -p /usr/local/openjdk13/bin
mkdir -p /usr/local/node-12.14.0/bin

ln -sf /usr/bin/python3 /usr/local/python-3.8.1/bin/python3
ln -sf /usr/bin/javac /usr/local/openjdk13/bin/javac
ln -sf /usr/bin/java /usr/local/openjdk13/bin/java
NODE_BIN="$(command -v node || command -v nodejs)"
ln -sf "$NODE_BIN" /usr/local/node-12.14.0/bin/node

echo "Compiler symlinks ready."
