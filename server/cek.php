<?php
	session_start();
	require 'koneksi.php';
	if(empty($_SESSION['username']) || !isset($_SESSION['level']) || !in_array($_SESSION['level'], ['Supervisor', 'Admin'])) {
		echo "<script>alert('Maaf, Anda tidak memiliki hak akses!');document.location='login.php'</script>";
	}
?>