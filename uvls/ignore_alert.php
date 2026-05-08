<?php
require 'koneksi.php';
require 'cek.php';

if (!isset($_GET['id']) || !isset($_GET['shift'])) {
    header('Location: index.php');
    exit;
}

$id_sheetsatu = (int)$_GET['id'];
$shift_ke     = (int)$_GET['shift'];

// Insert ignore jika belum ada
$sql = "
    INSERT INTO sheetsatu_ignore (id_sheetsatu, shift_ke, waktu_ignore)
    SELECT $id_sheetsatu, $shift_ke, NOW()
    FROM DUAL
    WHERE NOT EXISTS (
        SELECT 1 FROM sheetsatu_ignore 
        WHERE id_sheetsatu = $id_sheetsatu AND shift_ke = $shift_ke
    );
";

mysqli_query($koneksi, $sql);

// kembali ke halaman alert
header("Location: index.php");
exit;
