<?php 
require 'koneksi.php';
require 'cek.php';
?>
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>Daftar | User</title>

    <!-- Custom fonts for this template-->
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link
        href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i"
        rel="stylesheet">

    <!-- Custom styles for this template-->
    <link href="css/sb-admin-2.min.css" rel="stylesheet">

    <!-- Custom styles for this page -->
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">

</head>

<body id="page-top">

    <!-- Page Wrapper -->
    <div id="wrapper">

        <?php require 'sidebar.php';?>

        <!-- Content Wrapper -->
        <div id="content-wrapper" class="d-flex flex-column">

            <!-- Main Content -->
            <div id="content">

                <?php require 'topbar.php';?>
            
                <!-- Begin Page Content -->
                <div class="container-fluid">

                    <!-- DataTales Example -->
                    <div class="card shadow mb-4">
                        <div class="card-header py-3">
                        <h5 class="m-0 font-weight-bold text-primary">DATA USER</h5>
                        </div>
                    <br>

                    <!-- Button to Open the Modal -->
                    <div class="row ml-4">
                        <button type="button" class="btn btn-success" data-toggle="modal" data-target="#myModalTambah"><i class="fa fa-plus"> Data</i></button>
                    </div>
                    <br>
                 
    
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Username</th>
                                    <th>Password</th>
                                    <th>Level</th>
                                    <th>Aksi</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php
                                    $query = mysqli_query($koneksi,"SELECT * FROM login");
                                    $no = 1;
                                    while ($data = mysqli_fetch_assoc($query)) 
                                    {
                                ?>

                                <tr>
                                    <td><?php echo $data['id']?></td>
                                    <td><?php echo $data['username']?></td>
                                    <td><?php echo $data['password']?></td>
                                    <td><?php echo $data['level']?></td>
                                    <td>
                                    <!-- Button untuk modal -->
                                    <a href="#" type="button" class=" fa fa-edit btn btn-primary btn-md" data-toggle="modal" data-target="#myModal<?php echo $data['id']; ?>"></a>
                                    </td>
                                </tr>
                                    <!-- Modal Edit Mahasiswa-->
                                    <div class="modal fade" id="myModal<?php echo $data['id']; ?>" role="dialog">
                                        <div class="modal-dialog">

                                            <!-- Modal content-->
                                            <div class="modal-content">
                                                <div class="modal-header">
                                                    <h4 class="modal-title">Ubah Informasi Akun</h4>
                                                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                                                </div>

                                                <div class="modal-body">
                                                <form role="form" action="proses-edit-user.php" method="get">

                                                    <?php
                                                        $id = $data['id']; 
                                                        $query_edit = mysqli_query($koneksi,"SELECT * FROM login WHERE id='$id'");
                                                        //$result = mysqli_query($conn, $query);
                                                        while ($row = mysqli_fetch_array($query_edit)) {  
                                                    ?>

                                                    <input type="hidden" name="id" value="<?php echo $row['id']; ?>">

                                                    <div class="form-group">
                                                        <label>Username</label>
                                                        <input type="text" name="username" class="form-control" value="<?php echo $row['username']; ?> ">      
                                                    </div>

                                                    <div class="form-group">
                                                        <label>Passwword</label>
                                                        <input type="text" name="password" class="form-control" value="<?php echo $row['password']; ?> ">      
                                                    </div>

                                                    <div class="form-group">
                                                        Level :
                                                        <select class="form-control" name="level">
                                                        <option value="">-Level-</option>
                                                        <option>Supervisor</option>
                                                        <option>UT1</option>
                                                        <option>GUEST</option>
                                                        </select>
                                                    </div>

                                                    <div class="modal-footer">  
                                                        <button type="submit" class="btn btn-success">Ubah</button>
                                                        <a href="hapus-user.php?id=<?=$row['id'];?>" Onclick="confirm('Anda Yakin Ingin Menghapus?')" class="btn btn-danger">Hapus</a>
                                                        <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                                                    </div>
                                                    <?php 
                                                    }
                                                    //mysql_close($host);
                                                    ?>  

                                                </form>
                                            </div>
                                        </div>

                                    </div>
                                </div>
                                <?php
                                };
                                ?>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div> <!-- End of Container Fluid -->

                <!-- Modal Tambah -->
                <div id="myModalTambah" class="modal fade" role="dialog">
                    <div class="modal-dialog">

                        <!-- konten modal-->
                        <div class="modal-content">
                            <!-- heading modal -->
                            <div class="modal-header">
                                <h4 class="modal-title">Tambah Data User</h4>
		                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                            </div>

                            <!-- body modal -->
		                    <form action="tambah-user.php" method="get">
                                <div class="modal-body">
            
                                    Username :
                                    <input type="text" class="form-control"   name="username" required>

                                    Password :
                                    <input type="text" class="form-control"   name="password" required>

                                    Level :
                                    <select class="form-control" name="level">
                                        <option value="">-Level-</option>
                                        <option>Supervisor</option>
                                        <option>UT1</option>
                                        <option>GUEST</option>
                                    </select>
                                </div>
                                
                                <!-- footer modal -->
                                <div class="modal-footer">
		                            <button type="submit" class="btn btn-success" >Tambah</button>
                                    <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                                </div>
		                    </form>
                            
                        </div>
                    </div>
                </div>                  
            </div>
            <!-- End of Main Content -->

        </div>
        <!-- End of Content Wrapper -->

    </div>
    <!-- End of Page Wrapper -->

    <!-- Scroll to Top Button-->
    <a class="scroll-to-top rounded" href="#page-top">
        <i class="fas fa-angle-up"></i>
    </a>

    <!-- Logout Modal-->
    <?php require 'logout-modal.php';?>

    <!-- Bootstrap core JavaScript-->
    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>

    <!-- Core plugin JavaScript-->
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>

    <!-- Custom scripts for all pages-->
    <script src="js/sb-admin-2.min.js"></script>

    <!-- Page level plugins -->
    <script src="vendor/datatables/jquery.dataTables.min.js"></script>
    <script src="vendor/datatables/dataTables.bootstrap4.min.js"></script>

    <!-- Page level custom scripts -->
    <script src="js/demo/datatables-demo.js"></script>

</body>

</html>