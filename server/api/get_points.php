<?php
/**
 * Return list of gauge points for edge device config.
 * GET /api/get_points.php
 */
require_once __DIR__ . '/../koneksi.php';

header('Content-Type: application/json');

$q = mysqli_query($koneksi, "SELECT point, area, procces, item, min, max FROM sheetsatu WHERE tanggal IS NULL ORDER BY id ASC");
if (!$q) {
    http_response_code(500);
    echo json_encode(['error' => mysqli_error($koneksi)]);
    exit();
}

$points = [];
while ($row = mysqli_fetch_assoc($q)) {
    $points[] = $row;
}
echo json_encode($points);
