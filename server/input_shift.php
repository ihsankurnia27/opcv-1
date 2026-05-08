<?php
require 'koneksi.php';
require 'cek.php';

// Ambil data dari form
$shift_ke      = isset($_POST['shift_ke']) ? $_POST['shift_ke'] : '1';   // 1 / 2 / 3
$point         = isset($_POST['point']) ? $_POST['point'] : '';
$nilai_shift   = isset($_POST['nilai_shift']) ? $_POST['nilai_shift'] : '';
$remarks_shift = isset($_POST['remarks_shift']) ? $_POST['remarks_shift'] : '';
$tanggal       = isset($_POST['tanggal']) ? $_POST['tanggal'] : date('Y-m-d'); // dari hidden input di modal

// (opsional) ambil area, procces, item juga kalau mau dipakai di WHERE
$area    = isset($_POST['area']) ? $_POST['area'] : '';
$procces = isset($_POST['procces']) ? $_POST['procces'] : '';
$item    = isset($_POST['item']) ? $_POST['item'] : '';

// Sanitasi sederhana
$shift_ke      = (int)$shift_ke;
$point_sql     = mysqli_real_escape_string($koneksi, $point);
$nilai_sql     = mysqli_real_escape_string($koneksi, $nilai_shift);
$remarks_sql   = mysqli_real_escape_string($koneksi, $remarks_shift);
$tanggal_sql   = mysqli_real_escape_string($koneksi, $tanggal);
$area_sql      = mysqli_real_escape_string($koneksi, $area);
$procces_sql   = mysqli_real_escape_string($koneksi, $procces);
$item_sql      = mysqli_real_escape_string($koneksi, $item);

// Tentukan kolom shift, remarks, dan timestamp berdasarkan shift yang dipilih
if ($shift_ke === 1) {
    $kolom_shift  = 'shift_satu';
    $kolom_remark = 'remarks_satu';
    $kolom_time   = 't_satu';
} elseif ($shift_ke === 2) {
    $kolom_shift  = 'shift_dua';
    $kolom_remark = 'remarks_dua';
    $kolom_time   = 't_dua';
} else {
    $kolom_shift  = 'shift_tiga';
    $kolom_remark = 'remarks_tiga';
    $kolom_time   = 't_tiga';
}

// Query UPDATE berdasarkan point + tanggal
// (kalau mau lebih spesifik bisa tambahkan AND area = ... AND procces = ... AND item = ...)
$sql = "
    UPDATE sheetsatu
    SET 
        $kolom_shift  = '$nilai_sql',
        $kolom_remark = '$remarks_sql',
        $kolom_time   = NOW()
    WHERE 
        point   = '$point_sql'
        AND tanggal = '$tanggal_sql'
    LIMIT 1
";

$query = mysqli_query($koneksi, $sql);

// Redirect balik ke index.php dengan parameter tanggal & shift_ke
if ($query) {
    echo "<script>
            alert('Data shift berhasil disimpan');
            document.location='inputdata.php?tanggal=".$tanggal_sql."&shift_ke=".$shift_ke."';
          </script>";
} else {
    $err = mysqli_error($koneksi);
    echo "<script>
            alert('Gagal menyimpan data: ".addslashes($err)."');
            document.location='inputdata.php?tanggal=".$tanggal_sql."&shift_ke=".$shift_ke."';
          </script>";
}
