<?php
session_start();
// menghubungkan dengan koneksi
include 'koneksi.php';
 
// menangkap data yang dikirim dari form
$username = $_POST['username'];
$password = $_POST['password'];

//cek username terdaftar/tidak
$data = mysqli_query($koneksi, "SELECT * FROM login WHERE username='$username' and password='$password' ");
$cek = mysqli_num_rows($data);
 
//uji jika username terdaftar
if ($cek > 0) {
    $datas = mysqli_fetch_assoc($data);
        if ($datas['level'] == "Supervisor" || $datas['level'] == "Admin") {
        $_SESSION['username'] = $username;
        $_SESSION['level'] = $datas['level'];
        header("location:index.php");
    } else if ($datas['level'] == "UT1") {
        $_SESSION['username'] = $username;
        $_SESSION['level'] = "UT1";
        header("location:indexut1.php");
    } else if ($datas['level'] == "UT2") {
        $_SESSION['username'] = $username;
        $_SESSION['level'] = "UT2";
        header("location:indexut2.php");
    } else if ($datas['level'] == "GUEST") {
        $_SESSION['username'] = $username;
        $_SESSION['level'] = "GUEST";
        header("location:indexguest.php");
    }
     
} else {
    echo "<script>alert('Maaf, Username & Password Yang Anda Masukan Salah!');document.location='login.php'</script>";
}

?>