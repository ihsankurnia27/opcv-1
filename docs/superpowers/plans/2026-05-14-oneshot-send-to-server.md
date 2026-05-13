# One-Shot Send-to-Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After one-shot detection, user verifies annotated image + value, picks target point, then clicks "Send to Server" to push reading to the server API.

**Architecture:** Edge acts as proxy — browser POSTs to `/api/send-to-server`, edge forwards to server `receive_reading.php`. Server API key stays server-side. Point dropdown populated from existing `fetchPoints()` data that already hits `/api/points`.

**Tech Stack:** FastAPI, vanilla JS, CSS custom properties

**Key existing code:**
- `fetchPoints()` at line 1208 — fetches `/api/points`, populates config `#point` dropdown (called in init)
- `showResult(r)` at line 1103 — shows result card
- `hideResult()` at line 1113 — hides result card
- `init()` IIFE at line 1535 — calls `checkHealth()`, `loadConfig()`, `fetchVersion()`, `fetchPoints()`, `enumerateCameras()`

---

### Task 1: Backend endpoint — `POST /api/send-to-server`

**Files:**
- Modify: `edge/app/api.py` (insert after `/api/points` at line 659, before legacy aliases at line 662)
- Create: `edge/tests/test_api_send.py`

- [ ] **Step 1: Write the failing API test**

Create `edge/tests/test_api_send.py`:

```python
"""Test the /api/send-to-server endpoint."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_send_missing_fields_returns_422():
    resp = client.post("/api/send-to-server")
    assert resp.status_code in (400, 422)


def test_send_with_fields_returns_502():
    """server_api_url defaults to http://uvls-app/... which won't resolve in test."""
    resp = client.post("/api/send-to-server", data={
        "point": "TEST-001",
        "value": "5.2",
        "angle": "180.0",
        "annotated_image": "",
    })
    assert resp.status_code == 502
    assert any(w in resp.text for w in ["unreachable", "configured"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest edge/tests/test_api_send.py -v`
Expected: FAIL (no such endpoint, probably 404)

- [ ] **Step 3: Implement `POST /api/send-to-server` in api.py**

Insert after line 659 (end of `proxy_points()`), before the `# --- Legacy aliases ---` line (662):

```python
@app.post("/api/send-to-server")
def send_to_server(
    point: str = Form(...),
    value: float = Form(...),
    angle: float = Form(...),
    annotated_image: str = Form(""),
):
    cfg = load_config()
    url = cfg.get("server_api_url", "")
    if not url:
        raise HTTPException(400, "server_api_url not configured")

    payload = {
        "point": point,
        "value": value,
        "angle": angle,
        "annotated_image": annotated_image,
    }
    api_key = cfg.get("api_key", "")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(502, f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
    except urllib.error.URLError as e:
        raise HTTPException(502, str(e.reason))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest edge/tests/test_api_send.py -v`
Expected: both tests PASS (422 or 400 for missing fields, 502 for unreachable URL)

- [ ] **Step 5: Commit**

```bash
git add edge/app/api.py edge/tests/test_api_send.py
git commit -m "feat: add /api/send-to-server endpoint — proxy to server API"
```

---

### Task 2: Frontend — result actions UI

**Files:**
- Modify: `edge/app/static/index.html`

- [ ] **Step 1: Add result-actions HTML**

Insert after line 664 (`</div>` closing `result-layout`), inside `result-card` div, before the closing `</div>` of the card:

```html
        <div class="result-actions" id="result-actions" style="display:none">
          <select id="result-point" class="form-select"></select>
          <button class="btn btn-primary" id="btn-send" onclick="sendToServer()">Send to Server</button>
          <span id="send-status" class="send-status"></span>
        </div>
```

- [ ] **Step 2: Add CSS for new elements**

Insert after line 414 (the `@media` rule for `.result-layout`):

```css
.result-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.form-select {
  font-family: var(--font);
  font-size: .75rem;
  padding: 5px 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  min-width: 200px;
  flex: 1;
}

.send-status {
  font-size: .72rem;
  color: var(--text-muted);
  margin-left: auto;
}
```

- [ ] **Step 3: Add JS — global variables**

Find `let streamDetectActive` (around line 1044). After it, add:

```javascript
let lastResult = null;
let pointsList = [];
```

- [ ] **Step 4: Modify `fetchPoints()` — cache into pointsList**

In function `fetchPoints()` (line 1208), find the `r.forEach(p => { ... });` block (ends around line 1223). After it, before `if ([...sel.options].some(...))`, add:

```javascript
  pointsList = r;
```

- [ ] **Step 5: Modify `showResult(r)` — store result + populate dropdown**

Replace the function at line 1103:

```javascript
function showResult(r) {
  const card = q('result-card');
  card.style.display = 'block';
  q('result-img').src = 'data:image/jpeg;base64,' + r.annotated_image;
  q('result-img').style.display = 'block';
  q('result-data').textContent = JSON.stringify({value: r.value, angle: r.angle, center: r.center}, null, 2);
  q('result-data').style.display = 'block';
  q('result-summary').textContent = r.value + ' @ ' + r.angle + ' deg';
  lastResult = r;
  const sel = q('result-point');
  sel.innerHTML = '';
  pointsList.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.point;
    opt.textContent = p.point + ' | ' + (p.area||'') + ' | ' + (p.procces||'') + ' | ' + (p.item||'');
    sel.appendChild(opt);
  });
  if (sel.options.length === 0) {
    const cfgPt = q('point')?.value;
    if (cfgPt) { const o = document.createElement('option'); o.value = cfgPt; o.textContent = cfgPt; sel.appendChild(o); }
  }
  q('result-actions').style.display = 'flex';
}
```

- [ ] **Step 6: Modify `hideResult()` — also hide result-actions**

Replace the function at line 1113:

```javascript
function hideResult() {
  q('result-card').style.display = 'none';
  q('result-actions').style.display = 'none';
  lastResult = null;
  clearCanvas();
  resetHUD();
}
```

- [ ] **Step 7: Add `sendToServer()`**

Insert after `hideResult()` closing brace, before `// === One-shot ===` comment:

```javascript
async function sendToServer() {
  if (!lastResult) { toast('[FAIL] No result to send', 'error'); return; }
  const sel = q('result-point');
  if (!sel.value) { toast('[FAIL] Select a point first', 'error'); return; }
  const btn = q('btn-send');
  const status = q('send-status');
  btn.disabled = true;
  status.textContent = 'Sending...';
  try {
    const form = new FormData();
    form.append('point', sel.value);
    form.append('value', String(lastResult.value));
    form.append('angle', String(lastResult.angle));
    form.append('annotated_image', lastResult.annotated_image || '');
    const r = await fetch(API + '/api/send-to-server', { method: 'POST', body: form });
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    toast('[OK] Sent to server: ' + (data.status || data.message || 'ok'));
    status.textContent = 'Sent ✓';
  } catch(e) {
    toast('[FAIL] ' + e.message, 'error');
    status.textContent = 'Failed';
  } finally {
    btn.disabled = false;
  }
}
```

- [ ] **Step 8: Commit**

```bash
git add edge/app/static/index.html
git commit -m "feat: add send-to-server UI — point dropdown + verify-before-send flow"
```

---

### Task 3: Full integration smoke test

- [ ] **Step 1: Run existing test suite to confirm no regressions**

```bash
python -m pytest edge/tests/ -v
```

Expected: all ~30 tests pass

- [ ] **Step 2: Run new send-to-server tests**

```bash
python -m pytest edge/tests/test_api_send.py -v
```

Expected: both tests pass (422/400 + 502)

- [ ] **Step 3: Commit**

```bash
git add edge/app/api.py edge/tests/test_api_send.py edge/app/static/index.html
git commit -m "chore: finalize one-shot send-to-server feature"
```

---

### Deployment

```bash
git push origin main
sshpass -p orangepi ssh root@10.8.0.4 "cd /root/opcv-1 && git pull && cd /root/edge && docker compose up -d --build"
```
