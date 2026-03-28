# Frontend Code Quality Changes

## Summary

Added frontend code quality tooling (Prettier + ESLint) and applied consistent formatting to all frontend files.

---

## New Files

### `package.json`
- Defines dev dependencies: `prettier@^3`, `eslint@^8`
- npm scripts:
  - `npm run format` — auto-format all files under `frontend/`
  - `npm run format:check` — check formatting without writing (CI-safe)
  - `npm run lint` — lint `frontend/script.js` with ESLint
  - `npm run lint:fix` — auto-fix lint issues
  - `npm run quality` — run both `format:check` and `lint` together

### `.prettierrc`
- Prettier config: 2-space indent, single quotes, 100-char print width, LF line endings, ES5 trailing commas.

### `.eslintrc.json`
- ESLint config targeting browser + ES2021 globals.
- Key rules: `no-var` (error), `prefer-const` (warn), `eqeqeq` (error), `no-unused-vars` (warn).
- Marks `marked` (CDN-loaded library) as a known global to prevent false `no-undef` errors.

### `scripts/format-frontend.sh`
- Shell script that runs `npx prettier --write frontend/` — auto-formats all frontend files in one command.

### `scripts/check-frontend.sh`
- Shell script that runs Prettier check + ESLint in sequence; exits non-zero on any failure. Suitable for CI.

---

## Modified Files

### `frontend/script.js`, `frontend/style.css`, `frontend/index.html`
- Reformatted by Prettier to enforce consistent style: indentation, quote style, trailing commas, and line endings.

---

## Usage

```bash
# Install dev dependencies (one-time)
npm install

# Check formatting and lint
npm run quality
# or
./scripts/check-frontend.sh

# Auto-format
npm run format
# or
./scripts/format-frontend.sh
```
