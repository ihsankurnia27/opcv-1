<?php
require 'koneksi.php';
require 'cek.php';

// Ambil daftar point untuk dropdown upload
$qPoint = mysqli_query($koneksi, "SELECT point, area, procces, item FROM sheetsatu WHERE tanggal IS NULL ORDER BY id ASC");
$points = [];
while ($row = mysqli_fetch_assoc($qPoint)) {
    $points[] = $row;
}
$points_json = json_encode($points);

// Ambil 10 reading terbaru dari edge (ditandai remarks mengandung 'Edge gauge')
$qEdge = mysqli_query($koneksi, "SELECT point, shift_satu, shift_dua, shift_tiga, remarks_satu, remarks_dua, remarks_tiga, t_satu, t_dua, t_tiga, tanggal FROM sheetsatu WHERE remarks_satu LIKE '%Edge gauge%' OR remarks_dua LIKE '%Edge gauge%' OR remarks_tiga LIKE '%Edge gauge%' ORDER BY id DESC LIMIT 10");
$edge_readings = [];
while ($row = mysqli_fetch_assoc($qEdge)) {
    $edge_readings[] = $row;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Gauge Meter Reader</title>
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <style>
        .form-group label { font-weight: bold; font-size: 0.9em; }
        .form-text { font-size: 0.8em; color: #6c757d; }
        .config-section {
            background-color: #f8f9fc;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #e3e6f0;
        }
        .config-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #4e73df;
            margin-bottom: 15px;
            border-bottom: 2px solid #4e73df;
            padding-bottom: 5px;
        }
        .squared-tabs {
            border-bottom: 1px solid #dee2e6;
            padding-left: 0;
            margin-bottom: 15px !important;
        }
        .squared-tabs .nav-item {
            margin-bottom: -1px;
        }
        .squared-tabs .nav-link {
            border: 1px solid #dee2e6;
            border-radius: 0;
            padding: 8px 20px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
            border-bottom: 1px solid #dee2e6;
            margin-right: 2px;
        }
        .squared-tabs .nav-link.active {
            background: #fff;
            color: #4e73df;
            font-weight: 700;
            border-top: 2px solid #4e73df;
            border-bottom: 1px solid #fff;
        }
        .squared-tabs .nav-link:hover {
            color: #4e73df;
        }
    </style>
</head>
<body id="page-top">
    <div id="wrapper">
        <?php require 'sidebar.php'; ?>
        <div id="content-wrapper" class="d-flex flex-column">
            <div id="content">
                <?php require 'topbar.php'; ?>
                <div class="container-fluid">
                    <h1 class="h3 mb-4 text-gray-800">Gauge Meter Reader</h1>

                    <div class="row">
                        <div class="col-xl-7 col-lg-6">
                            <div class="card shadow mb-4">
                                <div class="card-header py-3">
                                    <h6 class="m-0 font-weight-bold text-primary">Deteksi & Monitoring</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="nav squared-tabs" role="tablist">
                                        <li class="nav-item">
                                            <a class="nav-link active" data-toggle="tab" href="#tab-upload">Upload Deteksi</a>
                                        </li>
                                        <li class="nav-item">
                                            <a class="nav-link" data-toggle="tab" href="#tab-edge">Edge Readings</a>
                                        </li>
                                    </ul>

                                    <div class="tab-content">
                                    <div class="tab-pane active" id="tab-upload">
                                        <div class="mt-2 p-3 border rounded bg-light">
                                            <h6 class="font-weight-bold">Upload Gambar</h6>
                                            <form id="uploadForm" action="proses_testing.php" method="POST" enctype="multipart/form-data" onsubmit="return confirmUpload()">
                                                <div class="form-group mb-2">
                                                    <select name="point" id="uploadPoint" class="form-control form-control-sm" required>
                                                        <option value="">-- Pilih Point --</option>
                                                    </select>
                                                </div>
                                                <div class="form-group mb-2">
                                                    <input type="file" name="gauge_image" accept="image/*" class="form-control-file form-control-sm" required>
                                                </div>
                                                <input type="hidden" name="center_offset_y" id="upload_center_offset" value="0">
                                                <input type="hidden" name="min_value" id="upload_min_value" value="0">
                                                <input type="hidden" name="max_value" id="upload_max_value" value="10">
                                                <input type="hidden" name="min_angle" id="upload_min_angle" value="45">
                                                <input type="hidden" name="max_angle" id="upload_max_angle" value="315">
                                                <input type="hidden" name="inner_ratio" id="upload_inner_ratio" value="0.60">
                                                <input type="hidden" name="outer_ratio" id="upload_outer_ratio" value="0.80">
                                                <input type="hidden" name="blur_kernel" id="upload_blur_kernel" value="5">
                                                <input type="hidden" name="threshold_block" id="upload_threshold_block" value="0">
                                                <input type="hidden" name="threshold_c" id="upload_threshold_c" value="5">
                                                <button type="submit" class="btn btn-sm btn-primary"><i class="fas fa-upload"></i> Upload & Deteksi</button>
                                            </form>
                                            <div id="uploadResult" class="mt-2 small"></div>
                                        </div>
                                    </div>

                                    <div class="tab-pane" id="tab-edge">
                                        <div class="mt-2">
                                            <p class="form-text">Reading terbaru dari edge device (Orange Pi).</p>
                                            <?php if (empty($edge_readings)): ?>
                                                <p class="text-muted small">Belum ada data dari edge device.</p>
                                            <?php else: ?>
                                                <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                                                <table class="table table-sm table-bordered small">
                                                    <thead class="thead-light">
                                                        <tr><th>Point</th><th>Nilai</th><th>Shift</th><th>Waktu</th></tr>
                                                    </thead>
                                                    <tbody>
                                                        <?php $shift_names = [1 => 'satu', 2 => 'dua', 3 => 'tiga']; ?>
                                                        <?php foreach ($edge_readings as $er): ?>
                                                            <?php foreach ($shift_names as $snum => $slabel):
                                                                $col_shift = 'shift_' . $slabel;
                                                                $col_time = 't_' . $slabel;
                                                                $col_remark = 'remarks_' . $slabel;
                                                                if (!empty($er[$col_shift]) && strpos($er[$col_remark] ?? '', 'Edge gauge') !== false): ?>
                                                                        <tr>
                                                                            <td><?= htmlspecialchars($er['point']) ?></td>
                                                                            <td><?= htmlspecialchars($er[$col_shift]) ?></td>
                                                                            <td><?= $snum ?></td>
                                                                            <td><?= htmlspecialchars($er[$col_time] ?? '-') ?></td>
                                                                        </tr>
                                                                <?php endif; ?>
                                                            <?php endforeach; ?>
                                                        <?php endforeach; ?>
                                                    </tbody>
                                                </table>
                                                </div>
                                            <?php endif; ?>
                                        </div>
                                    </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="col-xl-5 col-lg-6">
                            <div class="card shadow mb-4">
                                <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                    <h6 class="m-0 font-weight-bold text-primary">Konfigurasi Parameter</h6>
                                    <button class="btn btn-sm btn-outline-secondary" onclick="resetDefaults()">Reset Default</button>
                                </div>
                                <div class="card-body" style="max-height: 75vh; overflow-y: auto;">

                                    <div class="config-section">
                                        <div class="config-title">1. Kalibrasi Nilai & Sudut</div>
                                        <p class="form-text mb-3">Sesuaikan rentang nilai meteran dan sudut jarum (derajat).</p>
                                        <div class="row">
                                            <div class="col-md-6 form-group">
                                                <label>Nilai Minimum</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_minValue" value="0" step="any">
                                            </div>
                                            <div class="col-md-6 form-group">
                                                <label>Nilai Maksimum</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_maxValue" value="10" step="any">
                                            </div>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-6 form-group">
                                                <label>Sudut Minimum (&deg;)</label>
                                                <input type="range" class="custom-range" id="cfg_minAngle" min="0" max="360" value="45" oninput="document.getElementById('val_minAngle').innerText=this.value">
                                                <small class="form-text">Start angle (<span id="val_minAngle">45</span>&deg;)</small>
                                            </div>
                                            <div class="col-md-6 form-group">
                                                <label>Sudut Maksimum (&deg;)</label>
                                                <input type="range" class="custom-range" id="cfg_maxAngle" min="0" max="360" value="315" oninput="document.getElementById('val_maxAngle').innerText=this.value">
                                                <small class="form-text">End angle (<span id="val_maxAngle">315</span>&deg;)</small>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="config-section">
                                        <div class="config-title">2. Center Offset</div>
                                        <p class="form-text mb-3">Sesuaikan posisi vertikal center gauge.</p>
                                        <div class="form-group">
                                            <label>Y Offset (px)</label>
                                            <input type="range" class="custom-range" id="cfg_centerOffsetY" min="-50" max="50" value="0" oninput="document.getElementById('val_centerOffsetY').innerText=this.value">
                                            <small class="form-text">Center Y: <span id="val_centerOffsetY">0</span> px (positif = turun)</small>
                                        </div>
                                    </div>

                                    <div class="config-section">
                                        <div class="config-title">3. Radial Sampling (Deteksi Jarum)</div>
                                        <p class="form-text mb-3">Batas radius sampling jarum (% dari radius meteran).</p>
                                        <div class="row">
                                            <div class="col-md-6 form-group">
                                                <label>Radius Dalam (inner)</label>
                                                <input type="range" class="custom-range" id="cfg_innerRatio" min="0.1" max="0.9" step="0.05" value="0.60" oninput="document.getElementById('val_innerRatio').innerText=this.value">
                                                <small class="form-text">Mulai sampling: <span id="val_innerRatio">0.60</span></small>
                                            </div>
                                            <div class="col-md-6 form-group">
                                                <label>Radius Luar (outer)</label>
                                                <input type="range" class="custom-range" id="cfg_outerRatio" min="0.2" max="1.0" step="0.05" value="0.80" oninput="document.getElementById('val_outerRatio').innerText=this.value">
                                                <small class="form-text">Akhir sampling: <span id="val_outerRatio">0.80</span></small>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="config-section">
                                        <div class="config-title">4. Preprocessing (OpenCV)</div>
                                        <div class="row">
                                            <div class="col-md-6 form-group">
                                                <label>Blur Kernel</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_blurKernel" value="5" step="2" min="1" max="31">
                                                <small class="form-text">Gaussian blur kernel size (ganjil).</small>
                                            </div>
                                            <div class="col-md-6 form-group">
                                                <label>Adaptive Threshold Block</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_thresholdBlock" value="0" step="2" min="0" max="99">
                                                <small class="form-text">Block size untuk adaptive threshold.</small>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label>Threshold C (constant)</label>
                                            <input type="number" class="form-control form-control-sm" id="cfg_thresholdC" value="5" step="1" min="0" max="20">
                                            <small class="form-text">Konstanta kurangi mean lokal.</small>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <footer class="sticky-footer bg-white">
                <div class="container my-auto">
                    <div class="copyright text-center my-auto">
                        <span>Copyright &copy; Babang Youri</span>
                    </div>
                </div>
            </footer>
        </div>
    </div>

    <a class="scroll-to-top rounded" href="#page-top"><i class="fas fa-angle-up"></i></a>
    <?php require 'logout-modal.php'; ?>

    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="js/sb-admin-2.min.js"></script>

    <script type="text/javascript">
        // ==========================================
        // 1. DOM REFS & CONFIG
        // ==========================================

        let GAUGE_MIN_ANGLE_DEG = 45;
        let GAUGE_MAX_ANGLE_DEG = 315;
        let GAUGE_MIN_VALUE = 0.0;
        let GAUGE_MAX_VALUE = 10.0;
        let CENTER_OFFSET_Y = 0;
        let INNER_RATIO = 0.60;
        let OUTER_RATIO = 0.80;
        let BLUR_KERNEL = 5;
        let THRESHOLD_BLOCK = 0;
        let THRESHOLD_C = 5;

        const el_minVal = document.getElementById('cfg_minValue');
        const el_maxVal = document.getElementById('cfg_maxValue');
        const el_minAng = document.getElementById('cfg_minAngle');
        const el_maxAng = document.getElementById('cfg_maxAngle');
        const el_centerOffsetY = document.getElementById('cfg_centerOffsetY');
        const el_innerRatio = document.getElementById('cfg_innerRatio');
        const el_outerRatio = document.getElementById('cfg_outerRatio');
        const el_blurKernel = document.getElementById('cfg_blurKernel');
        const el_thresholdBlock = document.getElementById('cfg_thresholdBlock');
        const el_thresholdC = document.getElementById('cfg_thresholdC');

        async function saveParams() {
            const p = {
                minVal: el_minVal.value, maxVal: el_maxVal.value,
                minAng: el_minAng.value, maxAng: el_maxAng.value,
                centerOffsetY: el_centerOffsetY.value,
                innerRatio: el_innerRatio.value, outerRatio: el_outerRatio.value,
                blurKernel: el_blurKernel.value, thresholdBlock: el_thresholdBlock.value,
                thresholdC: el_thresholdC.value,
            };
            try {
                await fetch('save_gauge_config.php', {
                    method: 'POST', body: JSON.stringify(p),
                    headers: {'Content-Type': 'application/json'}
                });
            } catch (e) {}
        }

        async function loadParams() {
            try {
                const resp = await fetch('load_gauge_config.php');
                const p = await resp.json();
                if (!p || Object.keys(p).length === 0) return false;
                if (p.minVal !== undefined) el_minVal.value = p.minVal;
                if (p.maxVal !== undefined) el_maxVal.value = p.maxVal;
                if (p.minAng !== undefined) el_minAng.value = p.minAng;
                if (p.maxAng !== undefined) el_maxAng.value = p.maxAng;
                if (p.centerOffsetY !== undefined) el_centerOffsetY.value = p.centerOffsetY;
                if (p.innerRatio !== undefined) el_innerRatio.value = p.innerRatio;
                if (p.outerRatio !== undefined) el_outerRatio.value = p.outerRatio;
                if (p.blurKernel !== undefined) el_blurKernel.value = p.blurKernel;
                if (p.thresholdBlock !== undefined) el_thresholdBlock.value = p.thresholdBlock;
                if (p.thresholdC !== undefined) el_thresholdC.value = p.thresholdC;

                document.getElementById('val_minAngle').innerText = p.minAng ?? 45;
                document.getElementById('val_maxAngle').innerText = p.maxAng ?? 315;
                document.getElementById('val_centerOffsetY').innerText = p.centerOffsetY ?? 0;
                document.getElementById('val_innerRatio').innerText = p.innerRatio ?? '0.60';
                document.getElementById('val_outerRatio').innerText = p.outerRatio ?? '0.80';
                return true;
            } catch (e) { return false; }
        }

        function updateParamsFromUI() {
            GAUGE_MIN_VALUE = parseFloat(el_minVal.value);
            GAUGE_MAX_VALUE = parseFloat(el_maxVal.value);
            GAUGE_MIN_ANGLE_DEG = parseInt(el_minAng.value);
            GAUGE_MAX_ANGLE_DEG = parseInt(el_maxAng.value);
            CENTER_OFFSET_Y = parseInt(el_centerOffsetY.value);
            INNER_RATIO = parseFloat(el_innerRatio.value);
            OUTER_RATIO = parseFloat(el_outerRatio.value);
            BLUR_KERNEL = parseInt(el_blurKernel.value);
            if (BLUR_KERNEL % 2 === 0) BLUR_KERNEL++;
            THRESHOLD_BLOCK = parseInt(el_thresholdBlock.value);
            if (THRESHOLD_BLOCK % 2 === 0) THRESHOLD_BLOCK++;
            THRESHOLD_C = parseInt(el_thresholdC.value);

            document.getElementById('upload_center_offset').value = CENTER_OFFSET_Y;
            document.getElementById('upload_min_value').value = GAUGE_MIN_VALUE;
            document.getElementById('upload_max_value').value = GAUGE_MAX_VALUE;
            document.getElementById('upload_min_angle').value = GAUGE_MIN_ANGLE_DEG;
            document.getElementById('upload_max_angle').value = GAUGE_MAX_ANGLE_DEG;
            document.getElementById('upload_inner_ratio').value = INNER_RATIO;
            document.getElementById('upload_outer_ratio').value = OUTER_RATIO;
            document.getElementById('upload_blur_kernel').value = BLUR_KERNEL;
            document.getElementById('upload_threshold_block').value = THRESHOLD_BLOCK;
            document.getElementById('upload_threshold_c').value = THRESHOLD_C;

            saveParams();
        }

        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', updateParamsFromUI);
        });

        function applyDefaults() {
            el_minVal.value = 0; el_maxVal.value = 10;
            el_minAng.value = 45; el_maxAng.value = 315;
            el_centerOffsetY.value = 0;
            el_innerRatio.value = 0.60; el_outerRatio.value = 0.80;
            el_blurKernel.value = 5; el_thresholdBlock.value = 0; el_thresholdC.value = 5;

            document.getElementById('val_minAngle').innerText = 45;
            document.getElementById('val_maxAngle').innerText = 315;
            document.getElementById('val_centerOffsetY').innerText = '0';
            document.getElementById('val_innerRatio').innerText = '0.60';
            document.getElementById('val_outerRatio').innerText = '0.80';
        }

        function resetDefaults() {
            if (!confirm('Reset semua parameter ke default?')) return;
            applyDefaults();
            updateParamsFromUI();
        }

        // ==========================================
        // 2. UPLOAD — load point list + handle result
        // ==========================================
        const POINTS = <?= $points_json ?> || [];

        function loadUploadPoints() {
            const sel = document.getElementById('uploadPoint');
            if (!sel) return;
            POINTS.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.point;
                opt.textContent = p.point + ' | ' + p.area + ' | ' + p.procces + ' | ' + p.item;
                sel.appendChild(opt);
            });
        }

        function confirmUpload() {
            const sel = document.getElementById('uploadPoint');
            if (!sel.value) { alert('Pilih point dulu'); return false; }
            return true;
        }

        // Handle query params from proses_testing.php redirect
        const params = new URLSearchParams(window.location.search);
        if (params.get('success') === '1' || params.get('error')) {
            var uploadTab = document.querySelector('a[href="#tab-upload"]');
            if (uploadTab) $(uploadTab).tab('show');
        }
        if (params.get('success') === '1') {
            const val = params.get('value');
            const pt = params.get('point');
            const u = params.get('unit');
            const shift = params.get('shift');
            const img = params.get('image');
            const annotated = params.get('annotated');
            let html =
                `<div class="alert alert-success py-2 mb-2">
                    <strong>${pt}:</strong> ${val} ${u}
                    (Shift ${shift})
                </div>`;
            if (annotated) {
                html += `<div class="text-center"><a href="${annotated}" target="_blank">
                    <img src="${annotated}" class="img-fluid border rounded" style="max-height:300px" alt="annotated">
                </a></div>`;
            }
            document.getElementById('uploadResult').innerHTML = html;
        } else if (params.get('error')) {
            document.getElementById('uploadResult').innerHTML =
                `<div class="alert alert-danger py-2 mb-0">${params.get('error')}</div>`;
        }

        loadUploadPoints();

        // Init
        (async function init() {
            const loaded = await loadParams();
            if (!loaded) applyDefaults();
            updateParamsFromUI();
        })();
    </script>
</body>
</html>
