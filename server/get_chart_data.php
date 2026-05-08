<?php
require 'koneksi.php';

header('Content-Type: application/json');

if (!isset($_GET['start_date'], $_GET['end_date'], $_GET['point'])) {
    echo json_encode(['error' => 'Parameter tidak lengkap.']);
    exit;
}

$start_date = $_GET['start_date'];
$end_date   = $_GET['end_date'];
$point      = $_GET['point'];

// Sanitasi sederhana
$start_date = mysqli_real_escape_string($koneksi, $start_date);
$end_date   = mysqli_real_escape_string($koneksi, $end_date);
$point      = mysqli_real_escape_string($koneksi, $point);

/**
 * DI SINI PERUBAHANNYA:
 * - Kita pakai kolom `tanggal` (DATE) sebagai referensi tanggal,
 *   bukan lagi t_satu / t_dua / t_tiga.
 * - Jadi range yang dipilih user di index.php akan nyambung
 *   dengan tanggal yang di-input di inputdata.php
 */

$sql = "
    SELECT 
        tanggal,
        shift_satu,
        shift_dua,
        shift_tiga
    FROM sheetsatu
    WHERE point = '$point'
      AND tanggal BETWEEN '$start_date' AND '$end_date'
    ORDER BY tanggal ASC
";

$q = mysqli_query($koneksi, $sql);

if (!$q) {
    echo json_encode(['error' => 'Query gagal: ' . mysqli_error($koneksi)]);
    exit;
}

$labels   = [];
$data_s1  = [];
$data_s2  = [];
$data_s3  = [];
$rawData  = [];
$max_val  = 0;

while ($r = mysqli_fetch_assoc($q)) {
    // Pastikan format tanggal rapi (YYYY-MM-DD)
    $tgl = $r['tanggal'];

    $s1 = ($r['shift_satu'] !== null && $r['shift_satu'] !== '') ? floatval($r['shift_satu']) : null;
    $s2 = ($r['shift_dua']  !== null && $r['shift_dua']  !== '') ? floatval($r['shift_dua'])  : null;
    $s3 = ($r['shift_tiga'] !== null && $r['shift_tiga'] !== '') ? floatval($r['shift_tiga']) : null;

    $labels[]  = $tgl;
    $data_s1[] = $s1;
    $data_s2[] = $s2;
    $data_s3[] = $s3;

    $rawData[] = [
        'tanggal' => $tgl,
        's1'      => $s1 !== null ? $s1 : '-',
        's2'      => $s2 !== null ? $s2 : '-',
        's3'      => $s3 !== null ? $s3 : '-'
    ];

    foreach ([$s1, $s2, $s3] as $val) {
        if ($val !== null && $val > $max_val) {
            $max_val = $val;
        }
    }
}

if (empty($labels)) {
    echo json_encode([
        'error' => 'Tidak ada data untuk periode dan point tersebut.'
    ]);
    exit;
}

echo json_encode([
    'labels'   => $labels,   // akan dipakai jadi sumbu X
    'data_s1'  => $data_s1,
    'data_s2'  => $data_s2,
    'data_s3'  => $data_s3,
    'max_value'=> $max_val,
    'raw'      => $rawData
]);
