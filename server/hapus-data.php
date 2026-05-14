<?php
include 'koneksi.php';
require 'cek.php';

$id = $_GET['id'];
$type = $_GET['type'];

if ($type == 'template') {
    $stmt = mysqli_prepare($koneksi, "DELETE FROM sheetsatu WHERE id=? AND tanggal IS NULL");
    $redirect = 'data-templates.php';
} elseif ($type == 'reading') {
    $stmt = mysqli_prepare($koneksi, "DELETE FROM sheetsatu WHERE id=? AND tanggal IS NOT NULL");
    $redirect = 'data-readings.php';
} else {
    echo "ERROR: tipe tidak valid";
    exit;
}

mysqli_stmt_bind_param($stmt, "i", $id);

if (mysqli_stmt_execute($stmt)) {
    header("location:$redirect");
} else {
    echo "ERROR, data gagal dihapus: " . mysqli_error($koneksi);
}
?>
