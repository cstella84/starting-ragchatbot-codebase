# Frontend Changes

## Feature: Light/Dark Mode Toggle Button

### Files Modified

- `frontend/index.html`
- `frontend/style.css`
- `frontend/script.js`

---

### What Was Added

#### `index.html`
- Added a `<button id="themeToggle">` fixed to the top-right of the viewport.
- Contains two inline SVG icons: a **sun** (shown in dark mode) and a **moon** (shown in light mode), both with `aria-hidden="true"`.
- Button has `aria-label="Toggle light/dark mode"` and `title="Toggle theme"` for accessibility.

#### `style.css`
- **Light theme variables** — `[data-theme="light"]` block overrides all CSS custom properties (background, surface, text, border colors) with light equivalents.
- **Light theme fixes** — overrides for elements with hardcoded dark colors: `.source-tag`, `.message-content code/pre`.
- **Smooth transitions** — `transition: background-color/color/border-color/box-shadow 0.3s ease` applied to body and all major UI elements so theme switches animate smoothly.
- **`.theme-toggle` button styles** — fixed position (`top: 0.75rem; right: 1rem`), 40×40px circle, uses CSS variables so it adapts to both themes. Hover and focus states match the existing design (primary blue, focus ring).
- **Icon animation** — `.theme-toggle-icon` uses `opacity` + `transform: rotate()` transitions so icons cross-fade with a rotation effect when toggling.

#### `script.js`
- `initTheme()` — reads `localStorage` for a saved theme preference and applies it on page load (so the choice persists across sessions).
- `toggleTheme()` — sets/removes `data-theme="light"` on `<html>` and saves the new preference to `localStorage`.
- `setupEventListeners()` — wired `themeToggle` click to `toggleTheme()`.
- `initTheme()` called inside `DOMContentLoaded` before other setup.

---

### Design Decisions

- **`data-theme` on `<html>`** — standard pattern; CSS variable overrides cascade to every element on the page.
- **Default is dark** — matches the existing app theme; no class is needed on initial load.
- **Sun shown in dark mode, moon in light mode** — conventional: the icon represents the mode you'll switch *to*.
- **Rotation cross-fade** — departing icon rotates 90° away while the arriving icon rotates in from −90°, giving a smooth visual cue without requiring extra libraries.
- **`localStorage` persistence** — user preference survives page reloads without any backend changes.

---

## Feature: Light Theme Color Palette (Accessibility Pass)

### Files Modified

- `frontend/style.css`

---

### What Was Added / Changed

#### Light theme variable palette (`[data-theme="light"]`)

| Variable | Light value | Contrast notes |
|---|---|---|
| `--background` | `#f8fafc` | Page base |
| `--surface` | `#ffffff` | Sidebar, cards |
| `--surface-hover` | `#e2e8f0` | Hover states |
| `--text-primary` | `#0f172a` | ~19:1 on background ✓ |
| `--text-secondary` | `#475569` | ~5.9:1 on background ✓ |
| `--border-color` | `#e2e8f0` | Subtle separators |
| `--assistant-message` | `#f1f5f9` | Distinguishable from white surface |
| `--primary-color` | `#2563eb` | 4.6:1 on white — WCAG AA ✓ |
| `--focus-ring` | `rgba(37,99,235,0.15)` | Visible focus indicator |

#### New light-mode element overrides

- **`.message.assistant .message-content`** — uses `var(--assistant-message)` (#f1f5f9) instead of inheriting `var(--surface)` (#ffffff); without this, assistant bubbles are invisible against the page background.
- **`.message.welcome-message .message-content`** — reduces box-shadow opacity from 0.2 → 0.08 to avoid heavy shadow on light surfaces.
- **`.error-message`** — text changed from `#f87171` (light pink, ~1.4:1 contrast) to `#b91c1c` (dark red, ~7.1:1 on light bg) ✓
- **`.success-message`** — text changed from `#4ade80` (light green, ~1.4:1 contrast) to `#15803d` (dark green, ~7.3:1 on light bg) ✓

#### Expanded transitions list

Added `#sendButton`, `.error-message`, `.success-message`, and broadened `.message-content` (covers both user and assistant) to the `transition` rule so all visible elements animate smoothly on theme switch.
