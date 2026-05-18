# UI Scroll Container Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement independent scrolling for the parameter sidebar on wide screens while keeping the video feed visible.

**Architecture:** Wrap configuration cards in a sticky container for wide screens (>960px) using CSS `sticky` and `overflow-y: auto`.

**Tech Stack:** HTML, CSS.

---

### Task 1: Update CSS for Sticky Configuration Sidebar

**Files:**
- Modify: `edge/app/static/index.html`

- [ ] **Step 1: Locate CSS section and add sticky styling for `.config-col`**

```css
/* Update near line 235 */
/* MAIN GRID */
.main-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 16px;
  align-items: start;
  max-width: 1400px;
  margin: 0 auto;
}

/* Add this new media query block for PC only */
@media (min-width: 961px) {
  .config-col {
    position: sticky;
    top: 136px; /* Header (64px) + Toolbar (57px) + padding (15px) approx */
    height: calc(100vh - 152px); /* Viewport minus bars and padding */
    overflow-y: auto;
    padding-right: 8px; /* Space for scrollbar */
    /* Custom scrollbar for better look in MD3 */
    scrollbar-width: thin;
    scrollbar-color: var(--md-outline-variant) transparent;
  }
  .config-col::-webkit-scrollbar {
    width: 6px;
  }
  .config-col::-webkit-scrollbar-thumb {
    background-color: var(--md-outline-variant);
    border-radius: 10px;
  }
}
```

- [ ] **Step 2: Verify existing media query for mobile**

Ensure line 245 still exists to handle stacking on small screens:
```css
@media (max-width: 960px) {
  .main-grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 3: Commit changes**

```bash
git add edge/app/static/index.html
git commit -m "feat: add sticky scrollable container for config parameters on wide screens"
```
