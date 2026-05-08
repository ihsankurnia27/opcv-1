<?php
//koneksi
include('koneksi.php');

$username = $_GET['username'];
$password = $_GET['password'];
$level = $_GET['level'];

//query update
$query = mysqli_query($koneksi,"INSERT INTO `login` (`id`,`username`,`password`, `level`) VALUES (null,'$username','$password', '$level')");

if ($query) {
 # credirect ke page index
 header("location:user.php"); 
}
else{
 echo "ERROR, data gagal diupdate". mysqli_error($koneksi);
}

//mysql_close($host);
?>