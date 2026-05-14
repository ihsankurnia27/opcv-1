<?php
/**
 * Receive reading pushed from edge device.
 *
 * POST /api/receive_reading.php
 * Headers: Authorization: Bearer <api_key>
 * Body (JSON): {
 *   point: string,
 *   value: float,
 *   angle: float,
 *   unit: string,
 *   min: float,
 *   max: float,
 *   annotated_image: string (base64 JPEG, optional)
 * }
 *
 * Uses pre-shared API key from EDGE_API_KEY env var.
 * Detects shift from current server time and stores in sheetsatu.
 */

require_once __DIR__ . '/../koneksi.php';

// === AUTH ===
$expected_key = getenv('EDGE_API_KEY') ?: getenv('SERVER_API_KEY') ?: '';
if ($expected_key !== '') {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
    if (!preg_match('/^Bearer\s+(.+)$/i', $auth, $m) || $m[1] !== $expected_key) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['status' => 'error', 'message' => 'unauthorized']);
        exit();
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'POST only']);
    exit();
}

$input = json_decode(file_get_contents('php://input'), true);
if (!$input || empty($input['point']) || !isset($input['value'])) {
    http_response_code(400);
    header('Content-Type: application/json');
    echo json_encode(['status' => 'error', 'message' => 'missing point or value']);
    exit();
}

$point = preg_replace('/[^a-zA-Z0-9_\/\-\s.]/', '', $input['point']);
$value = (float) $input['value'];
$angle = isset($input['angle']) ? (float) $input['angle'] : null;
$unit = isset($input['unit']) ? preg_replace('/[^a-zA-Z0-9\/% ]/', '', $input['unit']) : '';
$gauge_min = isset($input['min']) ? (float) $input['min'] : 0;
$gauge_max = isset($input['max']) ? (float) $input['max'] : 100;

// === SAVE ANNOTATED IMAGE ===
$annotated_path = null;
if (!empty($input['annotated_image'])) {
    $image_data = base64_decode($input['annotated_image']);
    if ($image_data !== false) {
        $target_dir = __DIR__ . '/../uploads/';
        $filename = 'edge_' . uniqid() . '.jpg';
        file_put_contents($target_dir . $filename, $image_data);
        $annotated_path = 'uploads/' . $filename;
    }
}

// === SHIFT DETECTION (same logic as proses_testing.php) ===
$current_hour = (int) date('H');
if ($current_hour >= 6 && $current_hour < 14) {
    $kolom_shift = 'shift_satu';
    $kolom_remark = 'remarks_satu';
    $kolom_time = 't_satu';
    $shift_label = 1;
} elseif ($current_hour >= 14 && $current_hour < 22) {
    $kolom_shift = 'shift_dua';
    $kolom_remark = 'remarks_dua';
    $kolom_time = 't_dua';
    $shift_label = 2;
} else {
    $kolom_shift = 'shift_tiga';
    $kolom_remark = 'remarks_tiga';
    $kolom_time = 't_tiga';
    $shift_label = 3;
}

$today = date('Y-m-d');
$nilai_sql = mysqli_real_escape_string($koneksi, (string) $value);
$remarks_sql = mysqli_real_escape_string($koneksi, 'Edge gauge auto (angle: ' . ($angle ?? '?') . '°)');
$safe_point = mysqli_real_escape_string($koneksi, $point);

// === UPSERT ===
$check = mysqli_query($koneksi, "SELECT id, $kolom_shift FROM sheetsatu WHERE point = '$safe_point' AND tanggal = '$today' LIMIT 1");

if ($check && mysqli_num_rows($check) > 0) {
    $sql = "UPDATE sheetsatu SET
        $kolom_shift = '$nilai_sql',
        $kolom_remark = '$remarks_sql',
        $kolom_time = NOW()
        WHERE point = '$safe_point' AND tanggal = '$today'
        LIMIT 1";
} else {
    $tmpl = mysqli_query($koneksi, "SELECT area, procces, item, point, min, max, unit, freq FROM sheetsatu WHERE point = '$safe_point' AND tanggal IS NULL LIMIT 1");
    if ($tmpl_row = mysqli_fetch_assoc($tmpl)) {
        $area_sql = mysqli_real_escape_string($koneksi, $tmpl_row['area']);
        $procces_sql = mysqli_real_escape_string($koneksi, $tmpl_row['procces']);
        $item_sql = mysqli_real_escape_string($koneksi, $tmpl_row['item']);
        $min_sql = mysqli_real_escape_string($koneksi, $tmpl_row['min']);
        $max_sql = mysqli_real_escape_string($koneksi, $tmpl_row['max']);
        $unit_sql = mysqli_real_escape_string($koneksi, $tmpl_row['unit']);
        $freq_sql = mysqli_real_escape_string($koneksi, $tmpl_row['freq']);

        $sql = "INSERT INTO sheetsatu (area, procces, item, point, min, max, unit, freq,
                $kolom_shift, $kolom_remark, $kolom_time, tanggal)
                VALUES ('$area_sql', '$procces_sql', '$item_sql', '$safe_point',
                '$min_sql', '$max_sql', '$unit_sql', '$freq_sql',
                '$nilai_sql', '$remarks_sql', NOW(), '$today')";
    } else {
        $sql = "INSERT INTO sheetsatu (point, $kolom_shift, $kolom_remark, $kolom_time, tanggal)
                VALUES ('$safe_point', '$nilai_sql', '$remarks_sql', NOW(), '$today')";
    }
}

$ok = mysqli_query($koneksi, $sql);

header('Content-Type: application/json');
if ($ok) {
    echo json_encode([
        'status' => 'ok',
        'shift' => $shift_label,
        'point' => $point,
        'value' => $value,
        'image' => $annotated_path,
    ]);
} else {
    http_response_code(500);
    echo json_encode(['status' => 'error', 'message' => mysqli_error($koneksi)]);
}
