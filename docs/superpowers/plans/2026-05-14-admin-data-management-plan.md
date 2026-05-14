# Admin Data Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add DATA MANAGEMENT section to Admin/Supervisor sidebar with two CRUD pages for sheetsatu templates and daily readings.

**Architecture:** Two new PHP pages following existing `user.php` pattern (SB Admin 2 + DataTables). Four handler files for CUD operations. Sidebar modified to add new nav section.

**Tech Stack:** PHP 7+, MySQL, SB Admin 2 (Bootstrap 4 + jQuery), DataTables, FontAwesome 5

---

### Task 1: Modify sidebar navigation

**Files:**
- Modify: `server/sidebar.php` — insert DATA MANAGEMENT heading + two links after REKAP DATA entry (line 45)

- [ ] **Step 1: Add DATA MANAGEMENT section to sidebar**

Insert after line 45 (`</li>` closing REKAP DATA) and before line 47 (`<!-- Divider -->`):

```php
<!-- Nav Item - Data Templates -->
<li class="nav-item active">
    <a class="nav-link" href="data-templates.php">
    <i class="fas fa-fw fa-cog"></i>
        <span>DATA TEMPLATES</span>
    </a>
</li>

<!-- Nav Item - Data Readings -->
<li class="nav-item active">
    <a class="nav-link" href="data-readings.php">
    <i class="fas fa-fw fa-table"></i>
        <span>DATA READINGS</span>
    </a>
</li>
```

Also add a heading before these links. Insert after line 46 (`<!-- Divider -->`):

```php
<!-- Heading -->
<div class="sidebar-heading">
   DATA MANAGEMENT
</div>
```

- [ ] **Step 2: Verify the sidebar renders correctly**

Load any admin page and confirm the new nav items appear under "DATA MANAGEMENT" heading.

- [ ] **Step 3: Commit**

```bash
git add server/sidebar.php
git commit -m "feat: add DATA MANAGEMENT section to admin sidebar"
```

---

### Task 2: Create data-templates.php page

**Files:**
- Create: `server/data-templates.php`

This page lists all template rows (`tanggal IS NULL`) with Add, Edit, Delete. Same structure as `user.php`.

- [ ] **Step 1: Write the page**

Full page following `user.php` pattern. Key differences:
- Query: `SELECT * FROM sheetsatu WHERE tanggal IS NULL ORDER BY area, procces`
- Table columns: ID, Area, Process, Item, Point, Unit, Min, Max, Freq, Aksi
- Tambah modal: all 8 fields, POSTs to `proses-tambah-template.php`
- Edit modal: pre-filled form, POSTs to `proses-edit-template.php`
- Delete link: `hapus-data.php?id=ID&type=template` with JS confirm

```php
<?php 
require 'koneksi.php';
require 'cek.php';
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Data Templates</title>
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i" rel="stylesheet">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">
</head>

<body id="page-top">
    <div id="wrapper">
        <?php require 'sidebar.php';?>
        <div id="content-wrapper" class="d-flex flex-column">
            <div id="content">
                <?php require 'topbar.php';?>
                <div class="container-fluid">
                    <div class="card shadow mb-4">
                        <div class="card-header py-3">
                            <h5 class="m-0 font-weight-bold text-primary">DATA TEMPLATES</h5>
                        </div>
                        <br>
                        <div class="row ml-4">
                            <button type="button" class="btn btn-success" data-toggle="modal" data-target="#myModalTambah"><i class="fa fa-plus"> Template</i></button>
                        </div>
                        <br>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Area</th>
                                            <th>Process</th>
                                            <th>Item</th>
                                            <th>Point</th>
                                            <th>Unit</th>
                                            <th>Min</th>
                                            <th>Max</th>
                                            <th>Freq</th>
                                            <th>Aksi</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                        $query = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE tanggal IS NULL ORDER BY area, procces");
                                        while ($data = mysqli_fetch_assoc($query)) {
                                        ?>
                                        <tr>
                                            <td><?php echo $data['id']?></td>
                                            <td><?php echo htmlspecialchars($data['area'])?></td>
                                            <td><?php echo htmlspecialchars($data['procces'])?></td>
                                            <td><?php echo htmlspecialchars($data['item'])?></td>
                                            <td><?php echo htmlspecialchars($data['point'])?></td>
                                            <td><?php echo htmlspecialchars($data['unit'])?></td>
                                            <td><?php echo $data['min']?></td>
                                            <td><?php echo $data['max']?></td>
                                            <td><?php echo htmlspecialchars($data['freq'])?></td>
                                            <td>
                                                <a href="#" class="fa fa-edit btn btn-primary btn-md" data-toggle="modal" data-target="#myModal<?php echo $data['id']; ?>"></a>
                                            </td>
                                        </tr>
                                        <!-- Modal Edit -->
                                        <div class="modal fade" id="myModal<?php echo $data['id']; ?>" role="dialog">
                                            <div class="modal-dialog">
                                                <div class="modal-content">
                                                    <div class="modal-header">
                                                        <h4 class="modal-title">Edit Template</h4>
                                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                                    </div>
                                                    <div class="modal-body">
                                                        <form role="form" action="proses-edit-template.php" method="get">
                                                            <?php
                                                            $id = $data['id'];
                                                            $query_edit = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE id='$id'");
                                                            $row = mysqli_fetch_array($query_edit);
                                                            ?>
                                                            <input type="hidden" name="id" value="<?php echo $row['id']; ?>">
                                                            <div class="form-group">
                                                                <label>Area</label>
                                                                <input type="text" name="area" class="form-control" value="<?php echo htmlspecialchars($row['area']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Process</label>
                                                                <input type="text" name="procces" class="form-control" value="<?php echo htmlspecialchars($row['procces']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Item</label>
                                                                <input type="text" name="item" class="form-control" value="<?php echo htmlspecialchars($row['item']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Point</label>
                                                                <input type="text" name="point" class="form-control" value="<?php echo htmlspecialchars($row['point']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Unit</label>
                                                                <input type="text" name="unit" class="form-control" value="<?php echo htmlspecialchars($row['unit']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Min</label>
                                                                <input type="text" name="min" class="form-control" value="<?php echo $row['min']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Max</label>
                                                                <input type="text" name="max" class="form-control" value="<?php echo $row['max']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Freq</label>
                                                                <input type="text" name="freq" class="form-control" value="<?php echo htmlspecialchars($row['freq']); ?>">
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="submit" class="btn btn-success">Ubah</button>
                                                                <a href="hapus-data.php?id=<?=$row['id'];?>&type=template" onclick="return confirm('Anda Yakin Ingin Menghapus?')" class="btn btn-danger">Hapus</a>
                                                                <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <?php } ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Tambah -->
    <div id="myModalTambah" class="modal fade" role="dialog">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">Tambah Template</h4>
                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                </div>
                <form action="proses-tambah-template.php" method="get">
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Area</label>
                            <input type="text" class="form-control" name="area" required>
                        </div>
                        <div class="form-group">
                            <label>Process</label>
                            <input type="text" class="form-control" name="procces" required>
                        </div>
                        <div class="form-group">
                            <label>Item</label>
                            <input type="text" class="form-control" name="item" required>
                        </div>
                        <div class="form-group">
                            <label>Point</label>
                            <input type="text" class="form-control" name="point" required>
                        </div>
                        <div class="form-group">
                            <label>Unit</label>
                            <input type="text" class="form-control" name="unit" required>
                        </div>
                        <div class="form-group">
                            <label>Min</label>
                            <input type="text" class="form-control" name="min" required>
                        </div>
                        <div class="form-group">
                            <label>Max</label>
                            <input type="text" class="form-control" name="max" required>
                        </div>
                        <div class="form-group">
                            <label>Freq</label>
                            <input type="text" class="form-control" name="freq" required>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-success">Tambah</button>
                        <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <a class="scroll-to-top rounded" href="#page-top"><i class="fas fa-angle-up"></i></a>
    <?php require 'logout-modal.php';?>

    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="js/sb-admin-2.min.js"></script>
    <script src="vendor/datatables/jquery.dataTables.min.js"></script>
    <script src="vendor/datatables/dataTables.bootstrap4.min.js"></script>
    <script src="js/demo/datatables-demo.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add server/data-templates.php
git commit -m "feat: add data-templates.php page with CRUD UI"
```

---

### Task 3: Create data-readings.php page

**Files:**
- Create: `server/data-readings.php`

Lists daily reading rows (`tanggal IS NOT NULL`). Read + Edit + Delete. No Add button.

- [ ] **Step 1: Write the page**

Same structure as `data-templates.php` but:
- Query: `SELECT * FROM sheetsatu WHERE tanggal IS NOT NULL ORDER BY tanggal DESC`
- Edit modal: only shift values + remarks (area, item, point, tanggal as read-only labels)
- No Tambah modal
- Table columns: ID, Area, Item, Point, Tanggal, Shift 1, Remarks 1, Shift 2, Remarks 2, Shift 3, Remarks 3, Aksi

```php
<?php 
require 'koneksi.php';
require 'cek.php';
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Data Readings</title>
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i" rel="stylesheet">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">
</head>

<body id="page-top">
    <div id="wrapper">
        <?php require 'sidebar.php';?>
        <div id="content-wrapper" class="d-flex flex-column">
            <div id="content">
                <?php require 'topbar.php';?>
                <div class="container-fluid">
                    <div class="card shadow mb-4">
                        <div class="card-header py-3">
                            <h5 class="m-0 font-weight-bold text-primary">DATA READINGS</h5>
                        </div>
                        <br>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Area</th>
                                            <th>Item</th>
                                            <th>Point</th>
                                            <th>Tanggal</th>
                                            <th>Shift 1</th>
                                            <th>Remarks 1</th>
                                            <th>Shift 2</th>
                                            <th>Remarks 2</th>
                                            <th>Shift 3</th>
                                            <th>Remarks 3</th>
                                            <th>Aksi</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                        $query = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE tanggal IS NOT NULL ORDER BY tanggal DESC, area");
                                        while ($data = mysqli_fetch_assoc($query)) {
                                        ?>
                                        <tr>
                                            <td><?php echo $data['id']?></td>
                                            <td><?php echo htmlspecialchars($data['area'])?></td>
                                            <td><?php echo htmlspecialchars($data['item'])?></td>
                                            <td><?php echo htmlspecialchars($data['point'])?></td>
                                            <td><?php echo $data['tanggal']?></td>
                                            <td><?php echo $data['shift_satu']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_satu'])?></td>
                                            <td><?php echo $data['shift_dua']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_dua'])?></td>
                                            <td><?php echo $data['shift_tiga']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_tiga'])?></td>
                                            <td>
                                                <a href="#" class="fa fa-edit btn btn-primary btn-md" data-toggle="modal" data-target="#myModal<?php echo $data['id']; ?>"></a>
                                            </td>
                                        </tr>
                                        <!-- Modal Edit -->
                                        <div class="modal fade" id="myModal<?php echo $data['id']; ?>" role="dialog">
                                            <div class="modal-dialog">
                                                <div class="modal-content">
                                                    <div class="modal-header">
                                                        <h4 class="modal-title">Edit Reading</h4>
                                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                                    </div>
                                                    <div class="modal-body">
                                                        <form role="form" action="proses-edit-reading.php" method="get">
                                                            <?php
                                                            $id = $data['id'];
                                                            $query_edit = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE id='$id'");
                                                            $row = mysqli_fetch_array($query_edit);
                                                            ?>
                                                            <input type="hidden" name="id" value="<?php echo $row['id']; ?>">
                                                            <div class="form-group">
                                                                <label>Area</label>
                                                                <input type="text" class="form-control" value="<?php echo htmlspecialchars($row['area']); ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Item</label>
                                                                <input type="text" class="form-control" value="<?php echo htmlspecialchars($row['item']); ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Point</label>
                                                                <input type="text" class="form-control" value="<?php echo htmlspecialchars($row['point']); ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Tanggal</label>
                                                                <input type="text" class="form-control" value="<?php echo $row['tanggal']; ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 1</label>
                                                                <input type="text" name="shift_satu" class="form-control" value="<?php echo $row['shift_satu']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 1</label>
                                                                <input type="text" name="remarks_satu" class="form-control" value="<?php echo htmlspecialchars($row['remarks_satu']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 2</label>
                                                                <input type="text" name="shift_dua" class="form-control" value="<?php echo $row['shift_dua']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 2</label>
                                                                <input type="text" name="remarks_dua" class="form-control" value="<?php echo htmlspecialchars($row['remarks_dua']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 3</label>
                                                                <input type="text" name="shift_tiga" class="form-control" value="<?php echo $row['shift_tiga']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 3</label>
                                                                <input type="text" name="remarks_tiga" class="form-control" value="<?php echo htmlspecialchars($row['remarks_tiga']); ?>">
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="submit" class="btn btn-success">Ubah</button>
                                                                <a href="hapus-data.php?id=<?=$row['id'];?>&type=reading" onclick="return confirm('Anda Yakin Ingin Menghapus?')" class="btn btn-danger">Hapus</a>
                                                                <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <?php } ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <a class="scroll-to-top rounded" href="#page-top"><i class="fas fa-angle-up"></i></a>
    <?php require 'logout-modal.php';?>

    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="js/sb-admin-2.min.js"></script>
    <script src="vendor/datatables/jquery.dataTables.min.js"></script>
    <script src="vendor/datatables/dataTables.bootstrap4.min.js"></script>
    <script src="js/demo/datatables-demo.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add server/data-readings.php
git commit -m "feat: add data-readings.php page with edit/delete UI"
```

---

### Task 4: Create handler files (proses-tambah-template.php, proses-edit-template.php, proses-edit-reading.php, hapus-data.php)

**Files:**
- Create: `server/proses-tambah-template.php`
- Create: `server/proses-edit-template.php`
- Create: `server/proses-edit-reading.php`
- Create: `server/hapus-data.php`

- [ ] **Step 1: Create proses-tambah-template.php**

```php
<?php
include('koneksi.php');
require 'cek.php';

$area = $_GET['area'];
$procces = $_GET['procces'];
$item = $_GET['item'];
$point = $_GET['point'];
$unit = $_GET['unit'];
$min = $_GET['min'];
$max = $_GET['max'];
$freq = $_GET['freq'];

$query = mysqli_query($koneksi, "INSERT INTO sheetsatu (area, procces, item, point, unit, min, max, freq) VALUES ('$area', '$procces', '$item', '$point', '$unit', '$min', '$max', '$freq')");

if ($query) {
    header("location:data-templates.php");
} else {
    echo "ERROR, data gagal ditambah: " . mysqli_error($koneksi);
}
?>
```

- [ ] **Step 2: Create proses-edit-template.php**

```php
<?php
include('koneksi.php');
require 'cek.php';

$id = $_GET['id'];
$area = $_GET['area'];
$procces = $_GET['procces'];
$item = $_GET['item'];
$point = $_GET['point'];
$unit = $_GET['unit'];
$min = $_GET['min'];
$max = $_GET['max'];
$freq = $_GET['freq'];

$query = mysqli_query($koneksi, "UPDATE sheetsatu SET area='$area', procces='$procces', item='$item', point='$point', unit='$unit', min='$min', max='$max', freq='$freq' WHERE id='$id' AND tanggal IS NULL");

if ($query) {
    header("location:data-templates.php");
} else {
    echo "ERROR, data gagal diupdate: " . mysqli_error($koneksi);
}
?>
```

- [ ] **Step 3: Create proses-edit-reading.php**

```php
<?php
include('koneksi.php');
require 'cek.php';

$id = $_GET['id'];
$shift_satu = $_GET['shift_satu'];
$remarks_satu = $_GET['remarks_satu'];
$shift_dua = $_GET['shift_dua'];
$remarks_dua = $_GET['remarks_dua'];
$shift_tiga = $_GET['shift_tiga'];
$remarks_tiga = $_GET['remarks_tiga'];

$query = mysqli_query($koneksi, "UPDATE sheetsatu SET shift_satu='$shift_satu', remarks_satu='$remarks_satu', shift_dua='$shift_dua', remarks_dua='$remarks_dua', shift_tiga='$shift_tiga', remarks_tiga='$remarks_tiga' WHERE id='$id' AND tanggal IS NOT NULL");

if ($query) {
    header("location:data-readings.php");
} else {
    echo "ERROR, data gagal diupdate: " . mysqli_error($koneksi);
}
?>
```

- [ ] **Step 4: Create hapus-data.php**

```php
<?php
include('koneksi.php');
require 'cek.php';

$id = $_GET['id'];
$type = $_GET['type'];

if ($type == 'template') {
    $query = mysqli_query($koneksi, "DELETE FROM sheetsatu WHERE id='$id' AND tanggal IS NULL");
    $redirect = 'data-templates.php';
} elseif ($type == 'reading') {
    $query = mysqli_query($koneksi, "DELETE FROM sheetsatu WHERE id='$id' AND tanggal IS NOT NULL");
    $redirect = 'data-readings.php';
} else {
    echo "ERROR: tipe tidak valid";
    exit;
}

if ($query) {
    header("location:$redirect");
} else {
    echo "ERROR, data gagal dihapus: " . mysqli_error($koneksi);
}
?>
```

- [ ] **Step 5: Commit**

```bash
git add server/proses-tambah-template.php server/proses-edit-template.php server/proses-edit-reading.php server/hapus-data.php
git commit -m "feat: add CRUD handler files for data management"
```

---

### Task 5: Verify all pages load and render

- [ ] **Step 1: Quick syntax check**

```bash
cd server && php -l data-templates.php && php -l data-readings.php && php -l proses-tambah-template.php && php -l proses-edit-template.php && php -l proses-edit-reading.php && php -l hapus-data.php
```

Expected: `No syntax errors detected` for all files

- [ ] **Step 2: Load data-templates.php and data-readings.php in browser**

Open `http://localhost:8082/data-templates.php` and `http://localhost:8082/data-readings.php` (or whatever your dev URL is). Confirm:
- Pages render with SB Admin 2 layout
- DataTables loads and tables are populated
- Tambah modal opens on data-templates.php
- Edit modal opens for each row

---

### Self-Review

- **Spec coverage:** All spec requirements covered — sidebar nav, templates CRUD, readings edit/delete, handler files, type-guarded delete
- **Placeholder scan:** No TBD, TODO, or incomplete sections
- **Type consistency:** All file names, query params, and column names match across tasks
- **Existing pattern match:** Follows `user.php`, `tambah-user.php`, `hapus-user.php`, `proses-edit-user.php` patterns exactly
