<?php 
	session_start();
	require 'koneksi.php';
	if(empty($_SESSION['username']) or !isset($_SESSION['level']) or $_SESSION['level'] !== 'UT1') {
		echo "<script>alert('Maaf, Anda Harus Login!!');document.location='login.php'</script>";
	}
?>