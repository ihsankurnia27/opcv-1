<?php
require 'koneksi.php';

?>

<!DOCTYPE html>
<html lang="en">

<head>

  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <meta name="description" content="">
  <meta name="author" content="">

  <title>Login</title>

  <!-- Custom fonts for this template-->
  <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">


  <!-- Custom styles for this template-->
  <link href="css/sb-admin-2.min.css" rel="stylesheet">

</head>

<body style="background: linear-gradient(90deg, #FC466B 0%, #3F5EFB 100%);">

  <div class="container">

    <!-- Outer Row -->
    <div class="row justify-content-center">

      <div class="col-xl-5 col-lg-6 col-md-4">

        <div class="card o-hidden border-0 shadow-lg my-5">
            <!-- Nested Row within Card Body -->

                <div class="p-5">
                  <div class="text-center">
                    <h1 class="h4 text-gray-900 mb-4">SELAMAT DATANG!</h1>
                    <p>Silahkan login</p>
                  </div>
                  <form class="user" action="proses-login.php" method="post">
                    <div class="form-group">
                      <input type="username" name="username" class="form-control form-control-user" id="exampleInputUsername" placeholder="Masukan Username" required autofocus>
                    </div>
                    <div class="form-group">
                      <input type="password" name="password" class="form-control form-control-user" id="exampleInputPassword" placeholder="Masukan Password" required autofocus>
                    </div>
                    <input type="submit" name="login" class="btn btn-primary btn-user btn-block" value="Login">
                    <p class="mt-2 mb-3 text-muted text-center">Hubungi Supervisor! Jika Anda Lupa Password atau Belum Punya Akun! !</p>
                    <p class="mt-5 mb-1 text-muted text-center">&copy; 2025-<?=date('Y')?></p>
                  </form>
                  
                </div>

          </div>
      </div>

    </div>

  </div>

  <!-- Bootstrap core JavaScript-->
  <script src="vendor/jquery/jquery.min.js"></script>
  <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>

  <!-- Core plugin JavaScript-->
  <script src="vendor/jquery-easing/jquery.easing.min.js"></script>

  <!-- Custom scripts for all pages-->
  <script src="js/sb-admin-2.min.js"></script>

</body>

</html>
