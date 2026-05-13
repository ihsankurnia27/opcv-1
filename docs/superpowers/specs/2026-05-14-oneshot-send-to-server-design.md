# One-Shot Send-to-Server Design

> **Goal:** After one-shot detection, user verifies annotated image + value, picks target point, then sends to server.

## Architecture

```
One-shot click → detect (existing) → show annotated image + value
                                   → show point dropdown + [Send] button
User picks point, clicks Send → POST /api/send-to-server → edge proxies to server
                                                          → toast success/fail
```

Edge acts as proxy. Browser never sees server API key.

## Files

- **Modify:** `edge/app/api.py` — new endpoint
- **Modify:** `edge/app/static/index.html` — new result actions UI, JS changes

## Backend — `edge/app/api.py`

### New endpoint: `POST /api/send-to-server`

**Input (FormData):**
| Field | Type | Source |
|-------|------|--------|
| `point` | string | selected from dropdown |
| `value` | float | from detection result |
| `angle` | float | from detection result |
| `annotated_image` | string | base64 JPEG from detection result |

**Flow:**
1. Read config for `server_api_url` and `api_key`
2. Build payload: `{point, value, angle, annotated_image}`
3. POST JSON to server with `Authorization: Bearer <api_key>`
4. Return server response to browser

**Error cases:**
- 400: missing required fields
- 502: server_api_url not configured
- 502: server unreachable / HTTP error

Inline the HTTP call (not worth extracting shared module — `push_readings.py` is standalone CLI, `push_to_server` is 15 lines).

## Frontend — `edge/app/static/index.html`

### HTML additions

Inside `#result-card` div, after the `result-layout` div:

```html
<div class="result-actions" id="result-actions" style="display:none">
  <select id="result-point" class="form-select"></select>
  <button class="btn btn-primary" id="btn-send" onclick="sendToServer()">Send to Server</button>
  <span id="send-status" class="send-status"></span>
</div>
```

### CSS additions

Minimal additions matching brutalist-minimal style:
- `.result-actions` — flex row, gap, margin-top
- `.form-select` — border: 1px solid var(--border), no radius, system font, padding
- `.send-status` — small muted text for success/error inline feedback

### JS changes

**Global state:**
```javascript
let lastResult = null;        // stored detection result
let pointsList = [];          // cached point list from server
```

**`showResult(r)` — modified:**
- Set `lastResult = r`
- Populate `#result-point` dropdown from `pointsList` (or refetch if empty)
- Show `#result-actions`
- Select first point by default

**`hideResult()` — modified:**
- Hide `#result-actions` too
- Clear `lastResult`

**`sendToServer()` — new:**
- If no `lastResult`, toast error, return
- Get selected point from `#result-point`
- POST FormData with `{point, value, angle, annotated_image}` to `/api/send-to-server`
- On success: toast with server response status
- On error: toast with error message

**`init()` or page load — add:**
- Call `loadPoints()` to pre-fetch point list

**`loadPoints()` — new:**
- GET `/api/points`
- Cache in `pointsList`
- Populate any existing `#result-point` dropdown if visible

### Dropdown display

Show point name + area/process for clarity:
```
<option value="PG-1043">PG-1043 — Area A / Process B</option>
```

## No Changes
- `/api/one-shot` endpoint — unchanged
- `/api/points` endpoint — unchanged  
- `push_readings.py` — unchanged (separate interval-based path)
- Server `receive_reading.php` — unchanged
- CSS beyond the 3 additions above — unchanged

## Verification

1. Open `https://10.8.0.4:8765`
2. Start stream, click One-shot
3. Confirm annotated image + value appear
4. Confirm point dropdown is populated
5. Select a point, click "Send to Server"
6. Confirm toast shows server response
7. Check server `sheetsatu` table has the reading
8. Test error: stop server, try sending, confirm toast shows error
