<?php
include 'koneksi.php';
require 'cek.php';

$id = $_GET['id'];
$area = $_GET['area'];
$procces = $_GET['procces'];
$item = $_GET['item'];
$point = $_GET['point'];
$min = $_GET['min'];
$max = $_GET['max'];
$unit = $_GET['unit'];
$freq = $_GET['freq'];

$stmt = mysqli_prepare($koneksi, "UPDATE sheetsatu SET area=?, procces=?, item=?, point=?, min=?, max=?, unit=?, freq=? WHERE id=? AND tanggal IS NULL");
mysqli_stmt_bind_param($stmt, "ssssssssi", $area, $procces, $item, $point, $min, $max, $unit, $freq, $id);

if (mysqli_stmt_execute($stmt)) {
    header("location:data-templates.php");
} else {
    echo "ERROR, data gagal diupdate: " . mysqli_error($koneksi);
}
?>
