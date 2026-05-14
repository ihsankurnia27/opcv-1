<?php
include 'koneksi.php';
require 'cek.php';

$area = $_GET['area'];
$procces = $_GET['procces'];
$item = $_GET['item'];
$point = $_GET['point'];
$min = $_GET['min'];
$max = $_GET['max'];
$unit = $_GET['unit'];
$freq = $_GET['freq'];

$stmt = mysqli_prepare($koneksi, "INSERT INTO sheetsatu (area, procces, item, point, min, max, unit, freq) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
mysqli_stmt_bind_param($stmt, "ssssssss", $area, $procces, $item, $point, $min, $max, $unit, $freq);

if (mysqli_stmt_execute($stmt)) {
    header("location:data-templates.php");
} else {
    echo "ERROR, data gagal ditambah: " . mysqli_error($koneksi);
}
?>
