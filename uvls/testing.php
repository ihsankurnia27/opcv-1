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
        #videoInput { display: none; }
        #canvasOutput {
            border: 1px solid gray;
            margin-top: 10px;
            width: 100%;
            max-width: 640px;
            height: auto;
            background-color: #eee;
        }
        #output { margin-top: 20px; font-size: 1.5em; font-weight: bold; }
        .status { font-style: italic; color: #777; }
        .gauge-container { display: flex; flex-direction: column; align-items: center; }
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
        #fps-counter { font-size: 0.8em; color: #999; margin-top: 5px; }
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
                                    <h6 class="m-0 font-weight-bold text-primary">Live Feed & Deteksi</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="nav squared-tabs" role="tablist">
                                        <li class="nav-item">
                                            <a class="nav-link active" data-toggle="tab" href="#tab-live">Live Feed</a>
                                        </li>
                                        <li class="nav-item">
                                            <a class="nav-link" data-toggle="tab" href="#tab-upload">Upload Deteksi</a>
                                        </li>
                                    </ul>

                                    <div class="tab-content">
                                    <div class="tab-pane active" id="tab-live">
                                        <div class="gauge-container">
                                            <video id="videoInput" playsinline autoplay muted></video>
                                            <canvas id="canvasOutput" width="640" height="480"></canvas>
                                            <p class="status mt-3">Initializing camera...</p>
                                            <div id="output" class="text-success">Reading: -</div>
                                            <div id="fps-counter">0 fps</div>
                                        </div>
                                        <hr>
                                        <div class="text-muted small">
                                            <strong>Alur:</strong> Frame dikirim ke API Python (OpenCV) untuk deteksi jarum.<br>
                                            Hasil berupa gambar terannotasi + nilai numerik.
                                        </div>
                                    </div>

                                    <div class="tab-pane" id="tab-upload">
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

                                    <div class="config-section">
                                        <div class="config-title">5. Filter & Stabilitas Data</div>
                                        <p class="form-text mb-3">Median Filter + EMA + spike rejection.</p>
                                        <div class="row">
                                            <div class="col-md-6 form-group">
                                                <label>EMA Alpha (Responsiveness)</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_emaAlpha" value="0.15" step="0.05" min="0.01" max="1.0">
                                                <small class="form-text">0.1 = Smooth, 0.9 = Responsif</small>
                                            </div>
                                            <div class="col-md-6 form-group">
                                                <label>Max Jump Rejection</label>
                                                <input type="number" class="form-control form-control-sm" id="cfg_maxJump" value="1.5" step="0.1">
                                                <small class="form-text">Batas loncatan nilai (bar). Spike diabaikan.</small>
                                            </div>
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
        // 1. VALUE FILTER CLASS (sama seperti sebelumnya)
        // ==========================================
        class ValueFilter {
            constructor(medianWindowSize = 5, emaAlpha = 0.15, maxJump = 1.5) {
                this.rawBuffer = [];
                this.medianWindowSize = medianWindowSize;
                this.emaAlpha = emaAlpha;
                this.currentEMA = null;
                this.maxJump = maxJump;
                this.consecutiveJumps = 0;
            }

            updateParams(alpha, jump) {
                this.emaAlpha = alpha;
                this.maxJump = jump;
            }

            getMedian(arr) {
                const sorted = [...arr].sort((a, b) => a - b);
                const mid = Math.floor(sorted.length / 2);
                return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
            }

            add(rawValue) {
                if (this.currentEMA !== null) {
                    if (Math.abs(rawValue - this.currentEMA) > this.maxJump) {
                        this.consecutiveJumps++;
                        if (this.consecutiveJumps < 5) {
                            return this.currentEMA;
                        }
                    } else {
                        this.consecutiveJumps = 0;
                    }
                }

                this.rawBuffer.push(rawValue);
                if (this.rawBuffer.length > this.medianWindowSize) {
                    this.rawBuffer.shift();
                }
                const medianValue = this.getMedian(this.rawBuffer);

                if (this.currentEMA === null) {
                    this.currentEMA = medianValue;
                } else {
                    this.currentEMA = (this.emaAlpha * medianValue) + ((1 - this.emaAlpha) * this.currentEMA);
                }

                return this.currentEMA;
            }
        }

        const valueFilter = new ValueFilter();

        // ==========================================
        // 2. DOM REFS & CONFIG
        // ==========================================
        const video = document.getElementById('videoInput');
        const canvasOutput = document.getElementById('canvasOutput');
        const statusText = document.querySelector('.status');
        const outputDiv = document.getElementById('output');
        const fpsCounter = document.getElementById('fps-counter');

        const API_URL = 'proxy_detect.php';

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
        const el_emaAlpha = document.getElementById('cfg_emaAlpha');
        const el_maxJump = document.getElementById('cfg_maxJump');

        let pendingFrame = false;
        let detectCount = 0;
        let lastDetectFpsTime = performance.now();
        const DETECT_EVERY_N_FRAMES = 6;
        let frameCount = 0;

        async function saveParams() {
            const p = {
                minVal: el_minVal.value, maxVal: el_maxVal.value,
                minAng: el_minAng.value, maxAng: el_maxAng.value,
                centerOffsetY: el_centerOffsetY.value,
                innerRatio: el_innerRatio.value, outerRatio: el_outerRatio.value,
                blurKernel: el_blurKernel.value, thresholdBlock: el_thresholdBlock.value,
                thresholdC: el_thresholdC.value,
                emaAlpha: el_emaAlpha.value, maxJump: el_maxJump.value,
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
                if (p.emaAlpha !== undefined) el_emaAlpha.value = p.emaAlpha;
                if (p.maxJump !== undefined) el_maxJump.value = p.maxJump;

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

            valueFilter.updateParams(
                parseFloat(el_emaAlpha.value),
                parseFloat(el_maxJump.value)
            );
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
            el_emaAlpha.value = 0.15; el_maxJump.value = 1.5;

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
        // 3. CAMERA SETUP
        // ==========================================
        async function start() {
            try {

                // Check browser supports camera API
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                    statusText.innerHTML = "<span class='text-danger'>Kamera tidak tersedia. Akses via <b>localhost</b> atau <b>HTTPS</b>, atau browser tidak mendukung.</span>";
                    return;
                }

                let stream;
                try {
                    stream = await navigator.mediaDevices.getUserMedia({
                        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'environment' },
                        audio: false
                    });
                } catch (e) {
                    console.warn("Kamera belakang tidak ditemukan, mencoba kamera default...", e);
                    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                }

                video.srcObject = stream;
                await video.play();
                statusText.textContent = "Camera started. Memulai pipeline deteksi...";

                const actualWidth = video.videoWidth || 640;
                const actualHeight = video.videoHeight || 480;
                video.width = actualWidth;
                video.height = actualHeight;
                canvasOutput.width = actualWidth;
                canvasOutput.height = actualHeight;

                // Mulai loop — drawLoop handles detection pacing via frame counter
                requestAnimationFrame(drawLoop);
                detectLoop(); // first detection fires immediately

            } catch (err) {
                console.error("Error accessing camera: ", err);
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    statusText.innerHTML = "<span class='text-danger'>Error: Izin kamera ditolak.</span>";
                } else {
                    statusText.innerHTML = "<span class='text-danger'>Error Kamera: " + err.message + "</span>";
                }
            }
        }

        // ==========================================
        // 4. DRAW LOOP — raw video + needle overlay from JSON data
        // ==========================================
        let detection = null; // {cx, cy, radius, angle, value}

        function drawLoop() {
            const ctx = canvasOutput.getContext('2d');
            const w = canvasOutput.width;
            const h = canvasOutput.height;

            // Raw video
            ctx.drawImage(video, 0, 0, w, h);

            // Throttle detection every N frames (syncs with rAF naturally)
            frameCount++;
            if (frameCount >= DETECT_EVERY_N_FRAMES) {
                frameCount = 0;
                detectLoop();
            }

            // Overlay detection graphics from JSON data (no ghosting)
            if (detection) {
                const {cx, cy, radius, angle} = detection;

                // Gauge circle
                ctx.beginPath();
                ctx.arc(cx, cy, radius, 0, Math.PI * 2);
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                ctx.stroke();

                // Center dot
                ctx.beginPath();
                ctx.arc(cx, cy, 4, 0, Math.PI * 2);
                ctx.fillStyle = '#00ff00';
                ctx.fill();

                // Angle range arc (min → max)
                const minRad = GAUGE_MIN_ANGLE_DEG * Math.PI / 180;
                const maxRad = GAUGE_MAX_ANGLE_DEG * Math.PI / 180;
                ctx.beginPath();
                ctx.arc(cx, cy, radius * 0.75, minRad, maxRad);
                ctx.strokeStyle = '#ffff00';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
                ctx.stroke();
                ctx.setLineDash([]);

                // Start line (min angle)
                const startLen = radius * 0.7;
                ctx.beginPath();
                ctx.moveTo(cx, cy);
                ctx.lineTo(cx + startLen * Math.cos(minRad), cy + startLen * Math.sin(minRad));
                ctx.strokeStyle = '#00ffff';
                ctx.lineWidth = 1;
                ctx.stroke();

                // End line (max angle)
                ctx.beginPath();
                ctx.moveTo(cx, cy);
                ctx.lineTo(cx + startLen * Math.cos(maxRad), cy + startLen * Math.sin(maxRad));
                ctx.strokeStyle = '#00ffff';
                ctx.lineWidth = 1;
                ctx.stroke();

                // Radial sampling band (inner / outer ratio)
                const innerR = radius * INNER_RATIO;
                const outerR = radius * OUTER_RATIO;
                ctx.beginPath();
                ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
                ctx.strokeStyle = '#ff00ff';
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 5]);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(cx, cy, outerR, 0, Math.PI * 2);
                ctx.strokeStyle = '#ff00ff';
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.setLineDash([]);
                // Label between the circles
                ctx.fillStyle = '#ff00ff';
                ctx.font = '10px monospace';
                ctx.fillText('sampling', cx + 4, cy - outerR - 4);

                // Needle line
                const needleRad = angle * Math.PI / 180;
                const needleLen = radius * 0.85;
                const x2 = cx + needleLen * Math.cos(needleRad);
                const y2 = cy + needleLen * Math.sin(needleRad);
                ctx.beginPath();
                ctx.moveTo(cx, cy);
                ctx.lineTo(x2, y2);
                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 3;
                ctx.stroke();
            }

            requestAnimationFrame(drawLoop);
        }

        // ==========================================
        // 5. DETECT LOOP — capture dari offscreen canvas, kirim ke API
        // ==========================================
        async function detectLoop() {
            if (!pendingFrame) {
                pendingFrame = true;
                try {
                    // Capture raw video ke offscreen canvas (no overlay)
                    const offscreen = document.createElement('canvas');
                    offscreen.width = video.videoWidth || 640;
                    offscreen.height = video.videoHeight || 480;
                    const offCtx = offscreen.getContext('2d');
                    offCtx.drawImage(video, 0, 0);
                    const blob = await new Promise(resolve => offscreen.toBlob(resolve, 'image/jpeg', 0.92));

                    if (!blob) {
                        pendingFrame = false;
                        return;
                    }

                    const formData = new FormData();
                    formData.append('image', blob, 'frame.jpg');
                    formData.append('min_angle', String(GAUGE_MIN_ANGLE_DEG));
                    formData.append('max_angle', String(GAUGE_MAX_ANGLE_DEG));
                    formData.append('min_value', String(GAUGE_MIN_VALUE));
                    formData.append('max_value', String(GAUGE_MAX_VALUE));
                    formData.append('center_offset_y', String(CENTER_OFFSET_Y));
                    formData.append('inner_ratio', String(INNER_RATIO));
                    formData.append('outer_ratio', String(OUTER_RATIO));
                    formData.append('blur_kernel', String(BLUR_KERNEL));
                    formData.append('threshold_block', String(THRESHOLD_BLOCK));
                    formData.append('threshold_c', String(THRESHOLD_C));
                    formData.append('need_annotation', 'false');

                    const response = await fetch(API_URL, {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    detectCount++;
                    const now = performance.now();
                    if (now - lastDetectFpsTime >= 1000) {
                        fpsCounter.textContent = `${detectCount} det/s`;
                        detectCount = 0;
                        lastDetectFpsTime = now;
                    }

                    const data = await response.json();

                    if (data.error) {
                        statusText.textContent = `Error: ${data.error}`;
                        detection = null;
                    } else {
                        statusText.textContent = `Center (${data.center.x}, ${data.center.y}) R=${data.center.radius} | Needle ${data.angle}° | API min/max ${GAUGE_MIN_ANGLE_DEG}°/${GAUGE_MAX_ANGLE_DEG}°`;

                        // Store detection data for draw-loop overlay
                        detection = {
                            cx: data.center.x,
                            cy: data.center.y,
                            radius: data.center.radius,
                            angle: data.angle,
                        };

                        // Compute value client-side with proper wrap-around handling
                        if (data.angle !== null && data.angle !== undefined) {
                            let needleApi = data.angle;
                            let minA = GAUGE_MIN_ANGLE_DEG;
                            let maxA = GAUGE_MAX_ANGLE_DEG;
                            let minV = GAUGE_MIN_VALUE;
                            let maxV = GAUGE_MAX_VALUE;

                            // Handle wrap-around: ensure angle travel from min to max going clockwise
                            let rawVal;
                            if (minA <= maxA) {
                                // no wrap
                                rawVal = ((needleApi - minA) * (maxV - minV)) / (maxA - minA) + minV;
                            } else {
                                // wrap around 0: gauge sweeps past right (0°)
                                // equivalent to splitting: min→360 + 0→max
                                let fullRange = (360 - minA) + maxA;
                                let needlePos;
                                if (needleApi >= minA) {
                                    needlePos = needleApi - minA; // minA → 360
                                } else {
                                    needlePos = (360 - minA) + needleApi; // 0 → maxA
                                }
                                rawVal = (needlePos * (maxV - minV)) / fullRange + minV;
                            }

                            rawVal = Math.max(minV, Math.min(maxV, rawVal));

                            let stable = valueFilter.add(rawVal);
                            outputDiv.innerHTML = `Reading: <span style="font-size: 1.5em; color: #28a745;">${stable.toFixed(2)}</span> bar · <small>Angle ${data.angle}°</small>`;
                        }
                    }

                } catch (err) {
                    console.error('Detect error:', err);
                    statusText.textContent = `API Error: ${err.message}. Retrying...`;
                } finally {
                    pendingFrame = false;
                }
            }

        }

        // ==========================================
        // 6. UPLOAD FALLBACK — load point list + handle result
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
            // Switch to upload tab when result arrives
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
            document.getElementById('output').innerHTML =
                `Reading: <span style="font-size: 1.5em; color: #28a745;">${val}</span> ${u}`;
        } else if (params.get('error')) {
            document.getElementById('uploadResult').innerHTML =
                `<div class="alert alert-danger py-2 mb-0">${params.get('error')}</div>`;
        }

        loadUploadPoints();

        // Init params — fetch from server, fallback to defaults
        (async function init() {
            const loaded = await loadParams();
            if (!loaded) applyDefaults();
            updateParamsFromUI();

            // Mulai camera (hanya jalan di localhost/HTTPS)
            if (location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'https:') {
                start();
            } else {
                statusText.innerHTML = "Camera butuh localhost atau HTTPS. Gunakan form <b>Upload Gambar</b> di bawah.";
            }
        })();
    </script>
</body>
</html>
