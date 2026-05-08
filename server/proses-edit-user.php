<?php
//include('dbconnected.php');
include('koneksi.php');

$id = $_GET['id'];
$username = $_GET['username'];
$password = $_GET['password'];
$level = $_GET['level'];



//query update
$query = mysqli_query($koneksi,"UPDATE login SET username='$username', password='$password',level='$level' WHERE id='$id' ");

if ($query) {
 # credirect ke page index
 header("location:user.php"); 
}
else{
 echo "ERROR, data gagal diupdate". mysqli_error($koneksi);
}

//mysql_close($host);
?>