# Admin Data Management Tab — Design Spec

**Date:** 2026-05-14  
**Scope:** Server PHP app (`server/`)  
**Access:** Admin and Supervisor roles only

---

## Overview

Add a "DATA MANAGEMENT" section to the Admin/Supervisor sidebar with two pages:

1. **Data Templates** (`data-templates.php`) — full CRUD on `sheetsatu` master rows (`tanggal IS NULL`)
2. **Data Readings** (`data-readings.php`) — read, edit, and delete daily operator readings (`tanggal IS NOT NULL`)

---

## Architecture

Both pages follow the existing SB Admin 2 + DataTables pattern established by `user.php`. Both are guarded by `require 'cek.php'` (Admin/Supervisor only).

### Sidebar change (`sidebar.php`)

Insert a new heading + two links between the existing "REKAP DATA" and "INPUT DATA" entries:

```
DATA MANAGEMENT
  → Data Templates   (data-templates.php)
  → Data Readings    (data-readings.php)
```

---

## Pages

### data-templates.php

Manages `sheetsatu` rows where `tanggal IS NULL` (master gauge point definitions).

**Table columns:** area, process, item, point, unit, min, max, freq

**Actions:**
- "Tambah" button opens an Add modal with all 8 fields
- Each row has Edit (opens pre-filled modal) and Delete (JS confirm)

**Modals:**
- Add modal: form with inputs for all 8 fields, POSTs to `proses-tambah-template.php`
- Edit modal: same form pre-filled with row data, POSTs to `proses-edit-template.php`

**Queries:**
- List: `SELECT id, area, procces, item, point, unit, min, max, freq FROM sheetsatu WHERE tanggal IS NULL ORDER BY area, item`
- Insert: `INSERT INTO sheetsatu (area, procces, item, point, unit, min, max, freq) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
- Update: `UPDATE sheetsatu SET area=?, procces=?, item=?, point=?, unit=?, min=?, max=?, freq=? WHERE id=? AND tanggal IS NULL`
- Delete: `DELETE FROM sheetsatu WHERE id=? AND tanggal IS NULL`

---

### data-readings.php

Manages `sheetsatu` rows where `tanggal IS NOT NULL` (daily operator submissions).

**Table columns:** area, item, point, tanggal, shift 1 value, shift 2 value, shift 3 value, remarks (shift 1/2/3)

**Actions:**
- Each row has Edit (opens pre-filled modal) and Delete (JS confirm)
- No Add — daily rows are created by operators via `inputdata.php`

**Filters:** Date range picker (flatpickr, already available) + point name search, in addition to DataTables built-in search

**Edit modal fields:** shift_satu, remarks_satu, shift_dua, remarks_dua, shift_tiga, remarks_tiga (tanggal and point identity fields are read-only)

**Queries:**
- List: `SELECT id, area, item, point, tanggal, shift_satu, remarks_satu, shift_dua, remarks_dua, shift_tiga, remarks_tiga FROM sheetsatu WHERE tanggal IS NOT NULL ORDER BY tanggal DESC`
- Update: `UPDATE sheetsatu SET shift_satu=?, remarks_satu=?, shift_dua=?, remarks_dua=?, shift_tiga=?, remarks_tiga=? WHERE id=? AND tanggal IS NOT NULL`
- Delete: `DELETE FROM sheetsatu WHERE id=? AND tanggal IS NOT NULL`

---

## Handler Files

| File | Action | Table guard |
|------|--------|-------------|
| `proses-tambah-template.php` | INSERT template row | `tanggal IS NULL` enforced by not inserting tanggal |
| `proses-edit-template.php` | UPDATE template row | `AND tanggal IS NULL` in WHERE |
| `proses-edit-reading.php` | UPDATE reading row | `AND tanggal IS NOT NULL` in WHERE |
| `hapus-data.php` | DELETE row (both types) | `type` param: `template` or `reading` adds appropriate WHERE guard |

All handlers: `require 'koneksi.php'` + `require 'cek.php'`, use prepared statements (`mysqli_prepare`), redirect back to calling page on completion.

---

## Security Notes

- All handlers use `mysqli_prepare` + `bind_param` — no raw string interpolation
- `hapus-data.php` validates `type` param against an allowlist (`template`, `reading`) before building query
- `cek.php` guard on all pages and handlers ensures non-admin users get redirected
- ID params validated as integers before use

---

## Files to Create or Modify

| File | Change |
|------|--------|
| `sidebar.php` | Add DATA MANAGEMENT heading + two links |
| `data-templates.php` | New page |
| `data-readings.php` | New page |
| `proses-tambah-template.php` | New handler |
| `proses-edit-template.php` | New handler |
| `proses-edit-reading.php` | New handler |
| `hapus-data.php` | New handler |

Total: 1 modified, 6 new files.
