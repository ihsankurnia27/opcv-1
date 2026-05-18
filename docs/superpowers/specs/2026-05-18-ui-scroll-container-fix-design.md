---
name: ui-scroll-container-fix
description: Implement independent scrolling for the parameter sidebar on wide screens while keeping the video feed visible.
metadata:
  type: project
---

# UI Scroll Container Fix

Implement a sticky, scrollable container for the configuration parameters in the edge gauge UI. This applies only to wide screens (PC) to ensure that the video feed remains visible while the user scrolls through tuning parameters.

## Architecture

- **Target**: `edge/app/static/index.html`
- **Mechanism**: CSS `sticky` positioning with `overflow-y: auto`.

## Components

### Config Column (`.config-col`)
- Update `.config-col` style for wide screens (`min-width: 961px`).
- Set `position: sticky`.
- Set `top` to clear the app header and toolbar.
- Set `height` to `calc(100vh - height_of_bars)`.
- Enable `overflow-y: auto`.

## Data Flow
- No changes to data flow.

## Testing
- Verify scrolling behavior on desktop resolution (>960px).
- Verify that scrolling the parameters does not scroll the video feed.
- Verify that on mobile/small screens (<960px), the behavior remains unchanged (standard document flow).
