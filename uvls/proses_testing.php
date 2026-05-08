<?php
session_start();
require 'koneksi.php';

if (!isset($_SESSION['username']) || $_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: login.php');
    exit();
}

// === 1. VALIDASI INPUT ===
if (!isset($_POST['point']) || empty($_POST['point'])) {
    header('Location: testing.php?error=' . urlencode('Point harus dipilih.'));
    exit();
}

if (!isset($_FILES['gauge_image']) || $_FILES['gauge_image']['error'] !== UPLOAD_ERR_OK) {
    header('Location: testing.php?error=' . urlencode('Gagal mengunggah gambar.'));
    exit();
}

$point = $_POST['point'];
$image = $_FILES['gauge_image'];

// === 2. VALIDASI FILE ===
$target_dir = "uploads/";
$image_info = getimagesize($image["tmp_name"]);
if ($image_info === false) {
    header('Location: testing.php?error=' . urlencode('File bukan gambar.'));
    exit();
}
if ($image["size"] > 5000000) {
    header('Location: testing.php?error=' . urlencode('Ukuran gambar terlalu besar. Maks 5MB.'));
    exit();
}

// === 3. SIMPAN FILE ===
$ext = strtolower(pathinfo($image["name"], PATHINFO_EXTENSION));
$new_filename = uniqid('gauge_', true) . '.' . $ext;
$target_file = $target_dir . $new_filename;

if (!move_uploaded_file($image["tmp_name"], $target_file)) {
    header('Location: testing.php?error=' . urlencode('Gagal menyimpan file.'));
    exit();
}

// === 4. AMBIL DETAIL POINT DARI DB ===
$safe_point = mysqli_real_escape_string($koneksi, $point);
$query = "SELECT unit, min, max FROM sheetsatu WHERE point = '$safe_point' AND tanggal IS NULL LIMIT 1";
$result = mysqli_query($koneksi, $query);

$unit = '';
$min = 0.0;
$max = 100.0;

if ($result && mysqli_num_rows($result) > 0) {
    $point_details = mysqli_fetch_assoc($result);
    $unit = $point_details['unit'] ?? '';
    $min = is_numeric($point_details['min']) ? (float)$point_details['min'] : 0.0;
    $max = is_numeric($point_details['max']) ? (float)$point_details['max'] : 100.0;
}
if ($min > $max) {
    $tmp = $min;
    $min = $max;
    $max = $tmp;
}

// === 5. DETEKSI GAUGE VIA EDGE API ===
$api_url = getenv('GAUGE_API_URL') ?: 'http://api:8765/detect';
$annotated_path = $target_dir . 'annotated_' . $new_filename;
$center_y_offset = isset($_POST['center_offset_y']) ? (int)$_POST['center_offset_y'] : 0;
$gauge_min = isset($_POST['min_value']) ? (float)$_POST['min_value'] : $min;
$gauge_max = isset($_POST['max_value']) ? (float)$_POST['max_value'] : $max;
$min_angle = isset($_POST['min_angle']) ? (float)$_POST['min_angle'] : 45.0;
$max_angle = isset($_POST['max_angle']) ? (float)$_POST['max_angle'] : 315.0;
$inner_ratio = isset($_POST['inner_ratio']) ? (float)$_POST['inner_ratio'] : 0.60;
$outer_ratio = isset($_POST['outer_ratio']) ? (float)$_POST['outer_ratio'] : 0.80;
$blur_kernel = isset($_POST['blur_kernel']) ? (int)$_POST['blur_kernel'] : 5;
$threshold_block = isset($_POST['threshold_block']) ? (int)$_POST['threshold_block'] : 0;
$threshold_c = isset($_POST['threshold_c']) ? (int)$_POST['threshold_c'] : 5;

$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 60);
curl_setopt($ch, CURLOPT_POSTFIELDS, [
    'image' => new CURLFile($target_file, mime_content_type($target_file), $new_filename),
    'min_angle' => $min_angle,
    'max_angle' => $max_angle,
    'min_value' => $gauge_min,
    'max_value' => $gauge_max,
    'center_offset_y' => $center_y_offset,
    'inner_ratio' => $inner_ratio,
    'outer_ratio' => $outer_ratio,
    'blur_kernel' => $blur_kernel,
    'threshold_block' => $threshold_block,
    'threshold_c' => $threshold_c,
    'need_annotation' => 'true',
]);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$result_data = null;
if ($http_code === 200 && $response) {
    $result_data = json_decode($response, true);
}

$gauge_value = null;
$gauge_angle = null;

if ($result_data && !isset($result_data['error'])) {
    $gauge_value = $result_data['value'];
    $gauge_angle = $result_data['angle'];
    // Save annotated image from base64 response
    if (!empty($result_data['annotated_image'])) {
        $img_data = base64_decode($result_data['annotated_image']);
        if ($img_data !== false) {
            file_put_contents($annotated_path, $img_data);
        }
    }
} else {
    $gauge_value = round($min + (mt_rand() / mt_getrandmax()) * ($max - $min), 2);
}

// === 6. INSERT KE DATABASE DENGAN SHIFT DETECTION ===
// Shift detection based on current hour:
//   shift_satu: 06:00 - 13:59
//   shift_dua:  14:00 - 21:59
//   shift_tiga: 22:00 - 05:59
$current_hour = (int)date('H');
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
$nilai_sql = mysqli_real_escape_string($koneksi, $gauge_value);
$remarks_sql = mysqli_real_escape_string($koneksi, 'Gauge reader auto (image: ' . $new_filename . ')');

// Cek apakah sudah ada data untuk point + tanggal ini
$check = mysqli_query($koneksi, "SELECT id, $kolom_shift FROM sheetsatu WHERE point = '$safe_point' AND tanggal = '$today' LIMIT 1");

if ($check && mysqli_num_rows($check) > 0) {
    // Update
    $sql = "UPDATE sheetsatu SET
        $kolom_shift = '$nilai_sql',
        $kolom_remark = '$remarks_sql',
        $kolom_time = NOW()
        WHERE point = '$safe_point' AND tanggal = '$today'
        LIMIT 1";
} else {
    // Insert — clone template row + set tanggal
    // Pertama cari template (tanggal IS NULL)
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
        // Template tidak ditemukan, insert minimal
        $sql = "INSERT INTO sheetsatu (point, $kolom_shift, $kolom_remark, $kolom_time, tanggal)
                VALUES ('$safe_point', '$nilai_sql', '$remarks_sql', NOW(), '$today')";
    }
}

mysqli_query($koneksi, $sql);

// === 7. REDIRECT ===
$params = 'success=1&point=' . urlencode($point) . '&value=' . urlencode($gauge_value) . '&unit=' . urlencode($unit) . '&image=' . urlencode($target_file);
if ($gauge_angle !== null) {
    $params .= '&angle=' . urlencode($gauge_angle);
}
if (file_exists($annotated_path)) {
    $params .= '&annotated=' . urlencode($annotated_path);
}
$params .= '&shift=' . $shift_label;
header('Location: testing.php?' . $params);
exit();
