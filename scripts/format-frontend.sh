#!/usr/bin/env bash
# Auto-format all frontend files with Prettier
set -e

echo "==> Formatting frontend files (Prettier)..."
npx prettier --write frontend/

echo "==> Done."
