<?php 
require 'koneksi.php';
require 'cekguest.php';

// ================== 1. LOG 10 AKTIVITAS TERAKHIR ==================
$sql_recent = "
    SELECT point, shift_satu AS nilai, unit, remarks_satu AS remarks, t_satu AS waktu, 'Shift 1' AS shift_name
    FROM sheetsatu
    WHERE t_satu IS NOT NULL AND shift_satu IS NOT NULL AND shift_satu <> 0

    UNION ALL

    SELECT point, shift_dua AS nilai, unit, remarks_dua AS remarks, t_dua AS waktu, 'Shift 2' AS shift_name
    FROM sheetsatu
    WHERE t_dua IS NOT NULL AND shift_dua IS NOT NULL AND shift_dua <> 0

    UNION ALL

    SELECT point, shift_tiga AS nilai, unit, remarks_tiga AS remarks, t_tiga AS waktu, 'Shift 3' AS shift_name
    FROM sheetsatu
    WHERE t_tiga IS NOT NULL AND shift_tiga IS NOT NULL AND shift_tiga <> 0

    ORDER BY waktu DESC
    LIMIT 10
";
$q_recent = mysqli_query($koneksi, $sql_recent);

// ================== 2. FILTER BERDASARKAN TANGGAL ==================
$tanggal_filter = isset($_GET['tanggal_filter']) ? $_GET['tanggal_filter'] : '';
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $tanggal_filter)) {
    $tanggal_filter = '';
}

$sql_bydate = "
    SELECT point, nilai, unit, remarks, waktu, shift_name, tanggal FROM (
        SELECT point, shift_satu AS nilai, unit, remarks_satu AS remarks, 
               t_satu AS waktu, 'Shift 1' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_satu IS NOT NULL AND shift_satu IS NOT NULL AND shift_satu <> 0

        UNION ALL

        SELECT point, shift_dua AS nilai, unit, remarks_dua AS remarks, 
               t_dua AS waktu, 'Shift 2' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_dua IS NOT NULL AND shift_dua IS NOT NULL AND shift_dua <> 0

        UNION ALL

        SELECT point, shift_tiga AS nilai, unit, remarks_tiga AS remarks, 
               t_tiga AS waktu, 'Shift 3' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_tiga IS NOT NULL AND shift_tiga IS NOT NULL AND shift_tiga <> 0
    ) AS X
    WHERE 1=1
";

if ($tanggal_filter !== '') {
    $tanggal_safe = mysqli_real_escape_string($koneksi, $tanggal_filter);
    // filter pakai kolom tanggal, bukan DATE(waktu)
    $sql_bydate .= " AND tanggal = '$tanggal_safe' ";
}

$sql_bydate .= " ORDER BY waktu ASC";
$q_bydate = mysqli_query($koneksi, $sql_bydate);

// ================== 3. FILTER BERDASARKAN POINT & RENTANG WAKTU ==================

// daftar point untuk datalist
$q_pointlist = mysqli_query($koneksi, "SELECT DISTINCT point FROM sheetsatu ORDER BY point ASC");

$point_filter = isset($_GET['point_filter']) ? $_GET['point_filter'] : '';
$from_date    = isset($_GET['from_date']) ? $_GET['from_date'] : '';
$to_date      = isset($_GET['to_date']) ? $_GET['to_date'] : '';

if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $from_date)) $from_date = '';
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $to_date))   $to_date   = '';

$sql_by_point = "
    SELECT point, nilai, unit, remarks, waktu, shift_name, tanggal FROM (
        SELECT point, shift_satu AS nilai, unit, remarks_satu AS remarks, 
               t_satu AS waktu, 'Shift 1' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_satu IS NOT NULL AND shift_satu IS NOT NULL AND shift_satu <> 0

        UNION ALL

        SELECT point, shift_dua AS nilai, unit, remarks_dua AS remarks, 
               t_dua AS waktu, 'Shift 2' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_dua IS NOT NULL AND shift_dua IS NOT NULL AND shift_dua <> 0

        UNION ALL

        SELECT point, shift_tiga AS nilai, unit, remarks_tiga AS remarks, 
               t_tiga AS waktu, 'Shift 3' AS shift_name, tanggal
        FROM sheetsatu
        WHERE t_tiga IS NOT NULL AND shift_tiga IS NOT NULL AND shift_tiga <> 0
    ) AS X
    WHERE 1=1
";

if ($point_filter !== '') {
    $point_safe = mysqli_real_escape_string($koneksi, $point_filter);
    $sql_by_point .= " AND point = '$point_safe' ";
}

if ($from_date !== '') {
    $from_safe = mysqli_real_escape_string($koneksi, $from_date);
    // filter awal pakai kolom tanggal
    $sql_by_point .= " AND tanggal >= '$from_safe' ";
}

if ($to_date !== '') {
    $to_safe = mysqli_real_escape_string($koneksi, $to_date);
    // filter akhir pakai kolom tanggal
    $sql_by_point .= " AND tanggal <= '$to_safe' ";
}

$sql_by_point .= " ORDER BY waktu ASC";
$q_by_point = mysqli_query($koneksi, $sql_by_point);

?>
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <title>Variable Logsheet | Activity </title>

    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">

</head>

<body id="page-top">

<div id="wrapper">

<?php require 'sidebarguest.php';?>

<div id="content-wrapper" class="d-flex flex-column">

<div id="content">

<?php require 'topbar.php';?>

<div class="container-fluid">

    <!-- PANEL 1: 10 AKTIVITAS TERAKHIR -->
    <div class="card shadow mb-4">
        <div class="card-header py-3 d-flex justify-content-between align-items-center">
            <h5 class="m-0 font-weight-bold text-primary">Aktivitas Terbaru (10 Data Terakhir)</h5>
            
        </div>

        <div class="card-body">
            <div class="table-responsive" style="max-height: 320px; overflow-y: auto;">
                <table class="table table-bordered table-sm text-center" style="font-size: 12px;">
                    <thead class="thead-dark">
                        <tr>
                            <th>No</th>
                            <th>Point</th>
                            <th>Shift</th>
                            <th>Value</th>
                            <th>Unit</th>
                            <th>Remarks</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php
                        $no = 1;
                        while ($row = mysqli_fetch_assoc($q_recent)) {
                            $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';
                        ?>
                        <tr>
                            <td><?= $no++; ?></td>
                            <td><?= htmlspecialchars($row['point']); ?></td>
                            <td><?= htmlspecialchars($row['shift_name']); ?></td>
                            <td><?= htmlspecialchars($row['nilai']); ?></td>
                            <td><?= htmlspecialchars($row['unit']); ?></td>
                            <td><?= htmlspecialchars($row['remarks']); ?></td>
                            <td><?= htmlspecialchars($waktu); ?></td>
                        </tr>
                        <?php } ?>
                        <?php if ($no === 1) { ?>
                        <tr><td colspan="7">Belum ada aktivitas</td></tr>
                        <?php } ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- PANEL 2 & 3 DALAM 1 ROW -->
    <div class="row">

        <!-- PANEL 2: BERDASARKAN TANGGAL -->
        <div class="col-lg-6">
            <div class="card shadow mb-4">
                <div class="card-header py-3 d-flex justify-content-between align-items-center">
                    <h6 class="m-0 font-weight-bold text-primary">
                        Data Berdasarkan Tanggal
                    </h6>
                </div>

                <div class="card-body">

                    <form method="get" class="form-inline mb-3">
                        <label class="mr-2 font-weight-bold">Tanggal:</label>
                        <input type="date" name="tanggal_filter" class="form-control mr-2"
                               value="<?= htmlspecialchars($tanggal_filter); ?>">
                        <button type="submit" class="btn btn-primary btn-sm">
                            Tampilkan
                        </button>
                    </form>

                    <div class="table-responsive" style="max-height: 280px; overflow-y: auto;">
                        <table class="table table-bordered table-sm text-center" style="font-size: 11px;">
                            <thead class="thead-light">
                                <tr>
                                    <th>No</th>
                                    <th>Point</th>
                                    <th>Shift</th>
                                    <th>Value</th>
                                    <th>Unit</th>
                                    <th>Remarks</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php
                                $no2 = 1;
                                while ($row = mysqli_fetch_assoc($q_bydate)) {
                                    $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';
                                ?>
                                <tr>
                                    <td><?= $no2++; ?></td>
                                    <td><?= htmlspecialchars($row['point']); ?></td>
                                    <td><?= htmlspecialchars($row['shift_name']); ?></td>
                                    <td><?= htmlspecialchars($row['nilai']); ?></td>
                                    <td><?= htmlspecialchars($row['unit']); ?></td>
                                    <td><?= htmlspecialchars($row['remarks']); ?></td>
                                    <td><?= htmlspecialchars($waktu); ?></td>
                                </tr>
                                <?php } ?>
                                <?php if ($no2 === 1) { ?>
                                <tr><td colspan="7">Silakan pilih tanggal, atau belum ada data untuk tanggal tersebut.</td></tr>
                                <?php } ?>
                            </tbody>
                        </table>
                    </div>

                </div>
            </div>
        </div>

        <!-- PANEL 3: BERDASARKAN POINT & RENTANG WAKTU -->
        <div class="col-lg-6">
            <div class="card shadow mb-4">
                <div class="card-header py-3 d-flex justify-content-between align-items-center">
                    <h6 class="m-0 font-weight-bold text-primary">
                        Data Berdasarkan Point & Rentang Waktu
                    </h6>
                </div>

                <div class="card-body">

                    <form method="get" class="mb-3">

                        <div class="form-group">
                            <label class="font-weight-bold">Point:</label>
                            <input list="pointListFilter" name="point_filter" class="form-control"
                                   value="<?= htmlspecialchars($point_filter); ?>"
                                   placeholder="Ketik / pilih point...">
                            <datalist id="pointListFilter">
                                <?php while ($pf = mysqli_fetch_assoc($q_pointlist)) { ?>
                                    <option value="<?= htmlspecialchars($pf['point']); ?>"></option>
                                <?php } ?>
                            </datalist>
                        </div>

                        <div class="form-group">
                            <label class="font-weight-bold">Dari Tanggal:</label>
                            <input type="date" name="from_date" class="form-control"
                                   value="<?= htmlspecialchars($from_date); ?>">
                        </div>

                        <div class="form-group">
                            <label class="font-weight-bold">Sampai Tanggal:</label>
                            <input type="date" name="to_date" class="form-control"
                                   value="<?= htmlspecialchars($to_date); ?>">
                        </div>

                        <button type="submit" class="btn btn-primary btn-sm mt-2">
                            Tampilkan
                        </button>
                    </form>

                    <div class="table-responsive" style="max-height: 260px; overflow-y: auto;">
                        <table class="table table-bordered table-sm text-center" style="font-size: 11px;">
                            <thead class="thead-light">
                                <tr>
                                    <th>No</th>
                                    <th>Point</th>
                                    <th>Shift</th>
                                    <th>Value</th>
                                    <th>Unit</th>
                                    <th>Remarks</th>
                                    <th>Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php
                                $no3 = 1;
                                while ($row = mysqli_fetch_assoc($q_by_point)) {
                                    $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';
                                ?>
                                <tr>
                                    <td><?= $no3++; ?></td>
                                    <td><?= htmlspecialchars($row['point']); ?></td>
                                    <td><?= htmlspecialchars($row['shift_name']); ?></td>
                                    <td><?= htmlspecialchars($row['nilai']); ?></td>
                                    <td><?= htmlspecialchars($row['unit']); ?></td>
                                    <td><?= htmlspecialchars($row['remarks']); ?></td>
                                    <td><?= htmlspecialchars($waktu); ?></td>
                                </tr>
                                <?php } ?>
                                <?php if ($no3 === 1) { ?>
                                <tr><td colspan="7">Silakan pilih point dan rentang tanggal, atau belum ada data.</td></tr>
                                <?php } ?>
                            </tbody>
                        </table>
                    </div>

                </div>
            </div>
        </div>

    </div> <!-- end row -->
<!-- End of Page Wrapper -->

    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <?php require 'logout-modal.php';?>
</div> <!-- container-fluid -->

</div> <!-- content -->
</div> <!-- content-wrapper -->

</div> <!-- wrapper -->

<script src="vendor/jquery/jquery.min.js"></script>
<script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="js/sb-admin-2.min.js"></script>

</body>
</html>
