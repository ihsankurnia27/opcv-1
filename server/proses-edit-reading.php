<?php
include 'koneksi.php';
require 'cek.php';

$id = $_GET['id'];
$shift_satu = $_GET['shift_satu'];
$remarks_satu = $_GET['remarks_satu'];
$shift_dua = $_GET['shift_dua'];
$remarks_dua = $_GET['remarks_dua'];
$shift_tiga = $_GET['shift_tiga'];
$remarks_tiga = $_GET['remarks_tiga'];

$stmt = mysqli_prepare($koneksi, "UPDATE sheetsatu SET shift_satu=?, remarks_satu=?, shift_dua=?, remarks_dua=?, shift_tiga=?, remarks_tiga=? WHERE id=? AND tanggal IS NOT NULL");
mysqli_stmt_bind_param($stmt, "ssssssi", $shift_satu, $remarks_satu, $shift_dua, $remarks_dua, $shift_tiga, $remarks_tiga, $id);

if (mysqli_stmt_execute($stmt)) {
    header("location:data-readings.php");
} else {
    echo "ERROR, data gagal diupdate: " . mysqli_error($koneksi);
}
?>
