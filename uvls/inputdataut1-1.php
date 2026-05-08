<?php 
require 'koneksi.php';
require 'cekut1.php';

// ================== LOGIKA TANGGAL ==================

$tanggal_aktif = isset($_GET['tanggal']) && $_GET['tanggal'] != ''
    ? $_GET['tanggal']
    : date('Y-m-d');

if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $tanggal_aktif)) {
    $tanggal_aktif = date('Y-m-d');
}

// ================== TEMPLATE DATE CHECK ==================

$qCek = mysqli_query($koneksi, "SELECT COUNT(*) AS jml FROM sheetsatu WHERE tanggal = '$tanggal_aktif'");
$cek = mysqli_fetch_assoc($qCek);

if ($cek['jml'] == 0) {
    mysqli_query(
        $koneksi,
        "INSERT INTO sheetsatu
         (area, procces, item, point, tanggal, min, max, unit, freq,
          shift_satu, remarks_satu, t_satu,
          shift_dua, remarks_dua, t_dua,
          shift_tiga, remarks_tiga, t_tiga)
         SELECT 
             area, procces, item, point, '$tanggal_aktif',
             min, max, unit, freq,
             NULL, NULL, NULL,
             NULL, NULL, NULL,
             NULL, NULL, NULL
         FROM sheetsatu WHERE tanggal IS NULL"
    );
}

// ================== SHIFT ==================
$shift_aktif = isset($_GET['shift_ke']) ? $_GET['shift_ke'] : '1';

if ($shift_aktif == '1') {
    $kolom_shift  = 'shift_satu';
    $kolom_remark = 'remarks_satu';
    $judul_shift  = 'Shift 1';
    $shift_ke     = 1;
} elseif ($shift_aktif == '2') {
    $kolom_shift  = 'shift_dua';
    $kolom_remark = 'remarks_dua';
    $judul_shift  = 'Shift 2';
    $shift_ke     = 2;
} else {
    $kolom_shift  = 'shift_tiga';
    $kolom_remark = 'remarks_tiga';
    $judul_shift  = 'Shift 3';
    $shift_ke     = 3;
}

// ================== AMBIL DATA ==================
$qData = mysqli_query(
    $koneksi,
    "SELECT * FROM sheetsatu 
     WHERE tanggal = '$tanggal_aktif'
     ORDER BY id ASC"
);

$qPoint = mysqli_query(
    $koneksi,
    "SELECT * FROM sheetsatu WHERE tanggal IS NULL ORDER BY id ASC"
);

?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <title>Record | UVLS</title>

    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">
</head>

<body id="page-top">

<div id="wrapper">

<?php require 'sidebarut1.php'; ?>

<div id="content-wrapper" class="d-flex flex-column">
<div id="content">

<?php require 'topbar.php'; ?>

<div class="container-fluid">

    <!-- CARD JUDUL UTAMA -->
    <div class="card shadow mb-4">
        <div class="card-header py-3">
            <h4 class="m-0 font-weight-bold text-primary">
                UTILITY VARIABLE LOG SHEET
            </h4>
            <div style="height:2px;background:#4e73df;margin-top:6px;"></div>
        </div>
    </div>

    <!-- ================== CARD ATAS: TOMBOL TAMBAH DATA ================== -->
    <div class="card shadow mb-4">
        <div class="card-header py-3 d-flex justify-content-between align-items-center">
            <h5 class="m-0 font-weight-bold text-success">Tambah Data UVLS</h5>
            <button class="btn btn-success" data-toggle="modal" data-target="#modalTambah">
                <i class="fa fa-plus"></i> DATA
            </button>
        </div>
        <div class="card-body">
            <p class="mb-0">
                Gunakan tombol <strong>DATA</strong> di atas untuk menambahkan data baru.
                Tanggal dapat dipilih langsung di dalam form modal.
            </p>
        </div>
    </div>

    <!-- ================== CARD BAWAH: FILTER & TAMPILKAN DATA ================== -->
    <div class="card shadow mb-4">
        <div class="card-header py-3">
            <!-- FILTER TANGGAL & SHIFT -->
            <form method="get" class="form-inline">
                <label class="mr-2 font-weight-bold">Tanggal:</label>
                <input type="date" name="tanggal" 
                       class="form-control mr-3"
                       value="<?= $tanggal_aktif; ?>">

                <label class="mr-2 font-weight-bold">Shift:</label>
                <select name="shift_ke" class="form-control mr-3">
                    <option value="1" <?= ($shift_aktif=='1'?'selected':''); ?>>Shift 1</option>
                    <option value="2" <?= ($shift_aktif=='2'?'selected':''); ?>>Shift 2</option>
                    <option value="3" <?= ($shift_aktif=='3'?'selected':''); ?>>Shift 3</option>
                </select>

                <button type="submit" class="btn btn-primary">
                    Tampilkan
                </button>
            </form>

            <hr>

            <h5 class="m-0 font-weight-bold text-primary">
                Data <?= $judul_shift; ?> — <?= $tanggal_aktif; ?>
            </h5>
        </div>

        <div class="card-body">

            <table class="table table-bordered table-sm text-center" id="dataTable" width="100%">
                <thead class="thead-light">
                <tr>
                    <th>No</th>
                    <th>Area</th>
                    <th>Procces</th>
                    <th>Item</th>
                    <th>Point</th>
                    <th>Value</th>
                    <th>Unit</th>
                    <th>Remarks</th>
                    <th>Aksi</th>
                </tr>
                </thead>

                <tbody>

                <?php
                $no = 1;
                while($row = mysqli_fetch_assoc($qData)):
                ?>
                <tr>
                    <td><?= $no++; ?></td>
                    <td><?= htmlspecialchars($row['area']); ?></td>
                    <td><?= htmlspecialchars($row['procces']); ?></td>
                    <td><?= htmlspecialchars($row['item']); ?></td>
                    <td><?= htmlspecialchars($row['point']); ?></td>

                    <td><?= htmlspecialchars($row[$kolom_shift]); ?></td>
                    <td><?= htmlspecialchars($row['unit']); ?></td>
                    <td><?= htmlspecialchars($row[$kolom_remark]); ?></td>

                    <td>
                        <button class="btn btn-primary btn-sm"
                                data-toggle="modal"
                                data-target="#modalEdit<?= $row['id']; ?>">
                            <i class="fa fa-edit"></i>
                        </button>
                    </td>
                </tr>

                <!-- MODAL EDIT -->
                <div class="modal fade" id="modalEdit<?= $row['id']; ?>">
                    <div class="modal-dialog">
                        <div class="modal-content">

                            <div class="modal-header">
                                <h5 class="modal-title">Edit <?= htmlspecialchars($row['point']); ?></h5>
                                <button class="close" data-dismiss="modal">&times;</button>
                            </div>

                            <form action="edit_shiftut1-1.php" method="post">
                                <div class="modal-body">

                                    <input type="hidden" name="id" value="<?= $row['id']; ?>">
                                    <input type="hidden" name="shift_ke" value="<?= $shift_ke; ?>">
                                    <input type="hidden" name="tanggal" value="<?= $tanggal_aktif; ?>">

                                    <label>Nilai</label>
                                    <input type="number" name="nilai_shift" step="any" class="form-control"
                                           value="<?= htmlspecialchars($row[$kolom_shift]); ?>">

                                    <label class="mt-2">Remarks</label>
                                    <input type="text" name="remarks_shift" class="form-control"
                                           value="<?= htmlspecialchars($row[$kolom_remark]); ?>">

                                </div>

                                <div class="modal-footer">
                                    <button class="btn btn-success">Simpan</button>
                                </div>
                            </form>

                        </div>
                    </div>
                </div>

                <?php endwhile; ?>

                </tbody>
            </table>

        </div>

    </div>
    <!-- ================== END CARD TAMPIL & EDIT DATA ================== -->

</div> <!-- /.container-fluid -->

</div>
</div>

<!-- MODAL TAMBAH -->
<div class="modal fade" id="modalTambah">
<div class="modal-dialog">
<div class="modal-content">

    <div class="modal-header">
        <h5 class="modal-title">Input Data UVLS</h5>
        <button class="close" data-dismiss="modal">&times;</button>
    </div>

    <form action="input_shiftut1.php" method="post">
        <div class="modal-body">

            <!-- TANGGAL BISA DIISI USER -->
            <label class="font-weight-bold">Tanggal</label>
            <input type="date" 
                   name="tanggal" 
                   class="form-control" 
                   value="<?= $tanggal_aktif; ?>" 
                   required>

            <label class="mt-2 font-weight-bold">Shift</label>
            <select name="shift_ke" class="form-control">
                <option value="1" <?= ($shift_aktif=='1'?'selected':''); ?>>Shift 1</option>
                <option value="2" <?= ($shift_aktif=='2'?'selected':''); ?>>Shift 2</option>
                <option value="3" <?= ($shift_aktif=='3'?'selected':''); ?>>Shift 3</option>
            </select>

            <label class="mt-2 font-weight-bold">Point</label>
            <input list="pointList" name="point" class="form-control" required>

            <datalist id="pointList">
            <?php while($p = mysqli_fetch_assoc($qPoint)): ?>
                <option value="<?= htmlspecialchars($p['point']); ?>">
                    <?= $p['point']." | ".$p['area']." | ".$p['procces']." | ".$p['item']; ?>
                </option>
            <?php endwhile; ?>
            </datalist>

            <label class="mt-2 font-weight-bold">Nilai</label>
            <input type="number" name="nilai_shift" step="any" class="form-control">

            <label class="mt-2 font-weight-bold">Remarks</label>
            <input type="text" name="remarks_shift" class="form-control">

        </div>

        <div class="modal-footer">
            <button class="btn btn-success">Simpan</button>
        </div>
    </form>

</div>
</div>
</div>

<script src="vendor/jquery/jquery.min.js"></script>
<script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="vendor/datatables/jquery.dataTables.min.js"></script>
<script src="vendor/datatables/dataTables.bootstrap4.min.js"></script>
<script>
$(document).ready(function() {
    $('#dataTable').DataTable({
        pageLength: 25,
        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, "All"]
        ],
        ordering: false
    });
});
</script>
<!-- End of Page Wrapper -->
<script src="js/sb-admin-2.min.js"></script>
    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <?php require 'logout-modal.php';?>
</body>
</html>
