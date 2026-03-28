#!/usr/bin/env bash
# Run all frontend code quality checks
set -e

echo "==> Checking frontend formatting (Prettier)..."
npx prettier --check frontend/

echo "==> Linting frontend JS (ESLint)..."
npx eslint frontend/script.js

echo "==> All frontend quality checks passed."
