<?php
require 'koneksi.php';

if (!isset($_GET['id'])) {
    die('ID tidak diberikan.');
}

$id = (int) $_GET['id']; // casting ke integer untuk keamanan

// Hapus hanya satu baris berdasarkan ID di tabel sheetsatu_ignore
$sql = "DELETE FROM sheetsatu_ignore WHERE id = $id";

if (mysqli_query($koneksi, $sql)) {
    // Kembali ke halaman index setelah sukses
    header("Location: index.php?msg=unignored");
    exit();
} else {
    echo "Gagal meng-unignore data: " . mysqli_error($koneksi);
}
?>
