<?php 
require 'koneksi.php';
require 'cek.php';

// AMBIL DAFTAR POINT UNTUK DATALIST (PAKAI TEMPLATE: tanggal IS NULL)
$points = mysqli_query(
    $koneksi, 
    "SELECT id, area, procces, item, point 
     FROM sheetsatu 
     WHERE tanggal IS NULL 
     ORDER BY id"
);
?>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <title>ALERT LOGSHEET</title>

    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">

</head>

<body id="page-top">

<div id="wrapper">

<?php require 'sidebar.php';?>

<div id="content-wrapper" class="d-flex flex-column">
<div id="content">

<?php require 'topbar.php';?>

<div class="container-fluid">

    <div class="d-sm-flex align-items-center justify-content-between mb-4">
        <h1 class="h3 mb-0 text-gray-800">ALERT LOGSHEET</h1>
    </div>

    <!-- ================== CARD GRAFIK DATA SHEETSATU ================== -->
    <div class="row">
        <div class="col-xl-12 col-lg-12">
            <div class="card shadow mb-4">
                <div class="card-header py-3 d-flex align-items-center justify-content-between">
                    <h6 class="m-0 font-weight-bold text-primary">Grafik Data Utility</h6>
                </div>
                <div class="card-body">
                    <!-- Form Filter -->
                    <form id="formFilterGrafik" class="mb-3">
                        <div class="form-row">
                            <div class="form-group col-md-3">
                                <label for="start_date">Tanggal Awal</label>
                                <input type="date" id="start_date" name="start_date" class="form-control" required>
                            </div>
                            <div class="form-group col-md-3">
                                <label for="end_date">Tanggal Akhir</label>
                                <input type="date" id="end_date" name="end_date" class="form-control" required>
                            </div>
                            <div class="form-group col-md-4">
                                <label for="point_select">Point</label>
                                <!-- INPUT + DATALIST SUGGESTION (POINT | AREA | PROCCES | ITEM) -->
                                <input list="pointList" id="point_select" name="point" class="form-control" required>
                                <datalist id="pointList">
                                    <?php while($p = mysqli_fetch_assoc($points)) { ?>
                                        <option value="<?= htmlspecialchars($p['point']); ?>">
                                            <?= htmlspecialchars(
                                                $p['point']
                                                .' | '.$p['area']
                                                .' | '.$p['procces']
                                                .' | '.$p['item']
                                            ); ?>
                                        </option>
                                    <?php } ?>
                                </datalist>
                            </div>
                            <div class="form-group col-md-2 d-flex align-items-end">
                                <button type="button" id="btnTampilGrafik" class="btn btn-primary btn-block">
                                    Tampilkan Grafik
                                </button>
                            </div>
                        </div>
                    </form>

                    <!-- Canvas Grafik -->
                    <div style="height: 350px;">
                        <canvas id="alertChart"></canvas>
                    </div>
                    <small class="text-muted">
                        Grafik menampilkan urutan nilai Shift 1, Shift 2, dan Shift 3 per tanggal untuk point dan periode yang dipilih.
                    </small>

                    <hr>
                    <!-- Tabel Data Mentah -->
                    <h6 class="font-weight-bold">Data Nilai per Tanggal</h6>
                    <div class="table-responsive">
                        <table class="table table-bordered table-sm" style="font-size: 12px;" id="tableRaw">
                            <thead class="thead-dark">
                                <tr>
                                    <th>Tanggal</th>
                                    <th>Shift 1</th>
                                    <th>Shift 2</th>
                                    <th>Shift 3</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Diisi via AJAX -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- ================== END CARD GRAFIK ================== -->

    <!-- ================== CARD TABEL ALERT (ASLI) ================== -->
    <div class="row">
        <div class="col-xl-12 col-lg-12">
            <div class="card shadow mb-4">

                <div class="card-header py-3">
                    <h6 class="m-0 font-weight-bold text-primary">Data Alert Utility Variable Log Sheet</h6>
                </div>

                <div class="card-body">
                    <div class="table-responsive" style="max-height: 450px; overflow-y: auto;">
                        <table class="table table-bordered table-sm text-center" style="font-size: 12px;">
                            <thead class="thead-dark">
                                <tr>
                                    <th>No</th>
                                    <th>Point</th>
                                    <th>Shift</th>
                                    <th>Value</th>
                                    <th>Min</th>
                                    <th>Max</th>
                                    <th>Unit</th>
                                    <th>Remarks</th>
                                    <th>DateTime</th>
                                    <th>Action</th>
                                </tr>
                            </thead>

                            <tbody>
<?php

$sql = "
    SELECT 
        s.id AS id_sheetsatu,
        1 AS shift_ke,
        s.point,
        s.min,
        s.max,
        s.shift_satu AS nilai,
        s.unit,
        s.remarks_satu AS remarks,
        s.t_satu AS waktu
    FROM sheetsatu s
    LEFT JOIN sheetsatu_ignore ig 
        ON ig.id_sheetsatu = s.id AND ig.shift_ke = 1
    WHERE ig.id IS NULL
      AND s.shift_satu IS NOT NULL AND s.shift_satu <> 0
      AND (
            (s.remarks_satu IS NOT NULL AND s.remarks_satu <> '')
            OR
            (s.shift_satu < s.min OR s.shift_satu > s.max)
          )

    UNION ALL

    SELECT 
        s.id AS id_sheetsatu,
        2 AS shift_ke,
        s.point,
        s.min,
        s.max,
        s.shift_dua AS nilai,
        s.unit,
        s.remarks_dua AS remarks,
        s.t_dua AS waktu
    FROM sheetsatu s
    LEFT JOIN sheetsatu_ignore ig 
        ON ig.id_sheetsatu = s.id AND ig.shift_ke = 2
    WHERE ig.id IS NULL
      AND s.shift_dua IS NOT NULL AND s.shift_dua <> 0
      AND (
            (s.remarks_dua IS NOT NULL AND s.remarks_dua <> '')
            OR
            (s.shift_dua < s.min OR s.shift_dua > s.max)
          )

    UNION ALL

    SELECT 
        s.id AS id_sheetsatu,
        3 AS shift_ke,
        s.point,
        s.min,
        s.max,
        s.shift_tiga AS nilai,
        s.unit,
        s.remarks_tiga AS remarks,
        s.t_tiga AS waktu
    FROM sheetsatu s
    LEFT JOIN sheetsatu_ignore ig 
        ON ig.id_sheetsatu = s.id AND ig.shift_ke = 3
    WHERE ig.id IS NULL
      AND s.shift_tiga IS NOT NULL AND s.shift_tiga <> 0
      AND (
            (s.remarks_tiga IS NOT NULL AND s.remarks_tiga <> '')
            OR
            (s.shift_tiga < s.min OR s.shift_tiga > s.max)
          )

    ORDER BY waktu DESC
";

$query = mysqli_query($koneksi, $sql);
$no = 1;

while ($row = mysqli_fetch_assoc($query)) {
    $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';
?>
    <tr>
        <td><?= $no++; ?></td>
        <td><?= htmlspecialchars($row['point']); ?></td>
        <td><?= htmlspecialchars($row['shift_ke']); ?></td>
        <td><?= htmlspecialchars($row['nilai']); ?></td>
        <td><?= htmlspecialchars($row['min']); ?></td>
        <td><?= htmlspecialchars($row['max']); ?></td>
        <td><?= htmlspecialchars($row['unit']); ?></td>
        <td><?= htmlspecialchars($row['remarks']); ?></td>
        <td><?= htmlspecialchars($waktu); ?></td>
        <td>
            <!-- IGNORE -->
            <a href="ignore_alert.php?id=<?= $row['id_sheetsatu']; ?>&shift=<?= $row['shift_ke']; ?>"
               class="btn btn-warning btn-sm"
               onclick="return confirm('Ignore alert ini?');">
               Ignore
            </a>

            <!-- BUAT WR -->
            <a href="index.php?point=<?= urlencode($row['point']); ?>&shift=<?= $row['shift_ke']; ?>&nilai=<?= $row['nilai']; ?>"
   target="_blank"
   class="btn btn-info btn-sm ml-1">
   Buat WR
</a>

        </td>
    </tr>
<?php } ?>

                            </tbody>
                        </table>

                        <!-- LINK / TEKS UNTUK MELIHAT DATA YANG DI-IGNORE -->
                        <div class="mb-2">
                            <a href="#" class="text-primary" data-toggle="modal" data-target="#ignoredModal">
                                Lihat Data yang Di-ignore
                            </a>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>
    <!-- ================== END CARD TABEL ALERT ================== -->

</div> <!-- /.container-fluid -->
</div> <!-- /#content -->
</div> <!-- /#content-wrapper -->
</div> <!-- /#wrapper -->

<!-- MODAL: DATA YANG DI-IGNORE -->
<div class="modal fade" id="ignoredModal" tabindex="-1" role="dialog" aria-labelledby="ignoredModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-xl" role="document">
    <div class="modal-content">

      <div class="modal-header">
        <h5 class="modal-title" id="ignoredModalLabel">Data Alert yang Di-ignore</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <div class="modal-body">
        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
          <table class="table table-bordered table-sm text-center" style="font-size: 12px;">
            <thead class="thead-dark">
              <tr>
                <th>No</th>
                <th>Point</th>
                <th>Shift</th>
                <th>Value</th>
                <th>Min</th>
                <th>Max</th>
                <th>Unit</th>
                <th>Remarks</th>
                <th>DateTime</th>
                <th>Aksi</th>
              </tr>
            </thead>
            <tbody>
              <?php
                $sql_ignore = "
                  SELECT 
                      ig.id,
                      ig.shift_ke,
                      s.point,
                      s.min,
                      s.max,
                      CASE 
                        WHEN ig.shift_ke = 1 THEN s.shift_satu
                        WHEN ig.shift_ke = 2 THEN s.shift_dua
                        WHEN ig.shift_ke = 3 THEN s.shift_tiga
                      END AS nilai,
                      s.unit,
                      CASE 
                        WHEN ig.shift_ke = 1 THEN s.remarks_satu
                        WHEN ig.shift_ke = 2 THEN s.remarks_dua
                        WHEN ig.shift_ke = 3 THEN s.remarks_tiga
                      END AS remarks,
                      CASE 
                        WHEN ig.shift_ke = 1 THEN s.t_satu
                        WHEN ig.shift_ke = 2 THEN s.t_dua
                        WHEN ig.shift_ke = 3 THEN s.t_tiga
                      END AS waktu
                  FROM sheetsatu_ignore ig
                  JOIN sheetsatu s ON ig.id_sheetsatu = s.id
                  ORDER BY waktu DESC
                ";

                $q_ignore = mysqli_query($koneksi, $sql_ignore);
                $no2 = 1;
                while ($d = mysqli_fetch_assoc($q_ignore)) {
                  $waktu2 = $d['waktu'] ? date('Y-m-d H:i', strtotime($d['waktu'])) : '';
              ?>
              <tr>
                <td><?= $no2++; ?></td>
                <td><?= htmlspecialchars($d['point']); ?></td>
                <td><?= htmlspecialchars($d['shift_ke']); ?></td>
                <td><?= htmlspecialchars($d['nilai']); ?></td>
                <td><?= htmlspecialchars($d['min']); ?></td>
                <td><?= htmlspecialchars($d['max']); ?></td>
                <td><?= htmlspecialchars($d['unit']); ?></td>
                <td><?= htmlspecialchars($d['remarks']); ?></td>
                <td><?= htmlspecialchars($waktu2); ?></td>
                <td>
                  <a href="unignore.php?id=<?= $d['id']; ?>"
                     class="btn btn-danger btn-sm"
                     onclick="return confirm('Kembalikan alert ini?');">
                    Un-ignore
                  </a>
                </td>
              </tr>
              <?php } ?>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- Script JS -->
<script src="vendor/jquery/jquery.min.js"></script>
<script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="vendor/jquery-easing/jquery.easing.min.js"></script>
<script src="js/sb-admin-2.min.js"></script>

<!-- Chart.js -->
<script src="vendor/chart.js/Chart.min.js"></script>

<script>
    // Satu variabel global untuk chart
    var alertChart = null;

    // Helper: format Date to YYYY-MM-DD
    function formatDateYMD(d) {
        var yyyy = d.getFullYear();
        var mm = String(d.getMonth() + 1).padStart(2, '0');
        var dd = String(d.getDate()).padStart(2, '0');
        return yyyy + '-' + mm + '-' + dd;
    }

    // Function to load chart data via AJAX (dipakai oleh tombol dan auto-load)
    function loadChart(start_date, end_date, point) {
        // Validasi sederhana
        if (!start_date || !end_date || !point) {
            console.log('Parameter loadChart tidak lengkap');
            return;
        }

        $.ajax({
            url: 'get_chart_data.php',
            type: 'GET',
            dataType: 'json',
            data: {
                start_date: start_date,
                end_date: end_date,
                point: point
            },
            success: function(res) {
                if (res.error) {
                    alert(res.error);
                    return;
                }

                // Render Tabel Raw Data
                var tbody = $("#tableRaw tbody");
                tbody.empty();
                res.raw.forEach(function(row) {
                    tbody.append(`
                        <tr>
                            <td>${row.tanggal}</td>
                            <td>${row.s1}</td>
                            <td>${row.s2}</td>
                            <td>${row.s3}</td>
                        </tr>
                    `);
                });

                // Susun data satu garis: S1, S2, S3 berurutan per tanggal
                var xLabels = [];
                var yValues = [];

                for (var i = 0; i < res.labels.length; i++) {
                    var tgl = res.labels[i];

                    xLabels.push(tgl + ' (S1)');
                    xLabels.push(tgl + ' (S2)');
                    xLabels.push(tgl + ' (S3)');

                    yValues.push(res.data_s1[i]);
                    yValues.push(res.data_s2[i]);
                    yValues.push(res.data_s3[i]);
                }

                var ctx = document.getElementById('alertChart').getContext('2d');

                if (alertChart !== null) {
                    alertChart.destroy();
                }

                alertChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: xLabels,
                        datasets: [{
                            label: 'Nilai Shift 1, 2, 3 (berurutan)',
                            data: yValues,
                            borderColor: 'rgba(235, 54, 54, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            fill: false,
                            tension: 0.2,
                            pointRadius: 3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            yAxes: [{
                                ticks: {
                                    beginAtZero: true
                                },
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Nilai'
                                }
                            }],
                            xAxes: [{
                                scaleLabel: {
                                    display: true,
                                    labelString: 'Tanggal & Shift'
                                }
                            }]
                        },
                        tooltips: {
                            mode: 'index',
                            intersect: false
                        },
                        hover: {
                            mode: 'nearest',
                            intersect: true
                        }
                    }
                });
            },
            error: function(xhr, status, error) {
                console.log(error);
                alert('Gagal mengambil data grafik.');
            }
        });
    }

    // ============= AUTO-LOAD 5 HARI TERAKHIR UNTUK POINT LT-1101 SAAT HALAMAN DIBUKA =============
    $(document).ready(function () {
        // Set default point to LT-1101 (user masih bisa ganti di input jika ada)
        $('#point_select').val('LT-1101');

        // Hitung 5 hari kebelakang
        var today = new Date();
        var endDate = formatDateYMD(today);
        var past = new Date();
        past.setDate(today.getDate() - 6); // 4 hari sebelumnya -> total 5 hari termasuk hari ini
        var startDate = formatDateYMD(past);

        // Isi input tanggal agar user tahu range yang tampil
        $('#start_date').val(startDate);
        $('#end_date').val(endDate);

        // Panggil loadChart otomatis
        loadChart(startDate, endDate, 'LT-1101');
    });

    // Event klik tombol: gunakan fungsi yang sama
    $('#btnTampilGrafik').on('click', function() {
        var start_date = $('#start_date').val();
        var end_date   = $('#end_date').val();
        var point      = $('#point_select').val();

        if (!start_date || !end_date || !point) {
            alert('Lengkapi tanggal dan point dulu.');
            return;
        }

        loadChart(start_date, end_date, point);
    });
    
</script>
<!-- End of Page Wrapper -->

    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <?php require 'logout-modal.php';?>
</body>

</html>
