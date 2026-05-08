<?php 
require 'koneksi.php';
require 'cekut1.php';

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

<?php require 'sidebarut1.php';?>

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

    

  

</div> <!-- container-fluid -->

</div> <!-- content -->
<!-- End of Page Wrapper -->

    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <?php require 'logout-modal.php';?>
</div> <!-- content-wrapper -->

</div> <!-- wrapper -->

<script src="vendor/jquery/jquery.min.js"></script>
<script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="js/sb-admin-2.min.js"></script>

</body>
</html>
