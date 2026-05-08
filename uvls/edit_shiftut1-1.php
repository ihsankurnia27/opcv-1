<?php
require 'koneksi.php';
require 'cekut1.php';

$id            = $_POST['id'];
$shift_ke      = $_POST['shift_ke'];
$nilai_shift   = $_POST['nilai_shift'];
$remarks_shift = isset($_POST['remarks_shift']) ? $_POST['remarks_shift'] : '';

// Tentukan kolom shift, remarks, dan timestamp
if ($shift_ke == 1) {
    $kolom_shift  = 'shift_satu';
    $kolom_remark = 'remarks_satu';
    $kolom_time   = 't_satu';
} elseif ($shift_ke == 2) {
    $kolom_shift  = 'shift_dua';
    $kolom_remark = 'remarks_dua';
    $kolom_time   = 't_dua';
} else {
    $kolom_shift  = 'shift_tiga';
    $kolom_remark = 'remarks_tiga';
    $kolom_time   = 't_tiga';
}

// Update nilai, remarks, dan timestamp
$sql = "UPDATE sheetsatu
        SET $kolom_shift  = '$nilai_shift',
            $kolom_remark = '$remarks_shift',
            $kolom_time   = NOW()
        WHERE id = '$id'
        LIMIT 1";

$query = mysqli_query($koneksi, $sql);

if ($query) {
    echo "<script>
            alert('Data berhasil diupdate');
            document.location='inputdataut1-1.php?shift_ke=$shift_ke';
          </script>";
} else {
    echo "<script>
            alert('Gagal mengupdate data');
            document.location='inputdataut1-1.php?shift_ke=$shift_ke';
          </script>";
}
