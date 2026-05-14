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
    <title>Data Templates</title>
    <link href="vendor/fontawesome-free/css/all.min.css" rel="stylesheet" type="text/css">
    <link href="https://fonts.googleapis.com/css?family=Nunito:200,200i,300,300i,400,400i,600,600i,700,700i,800,800i,900,900i" rel="stylesheet">
    <link href="css/sb-admin-2.min.css" rel="stylesheet">
    <link href="vendor/datatables/dataTables.bootstrap4.min.css" rel="stylesheet">
</head>

<body id="page-top">
    <div id="wrapper">
        <?php require 'sidebar.php';?>
        <div id="content-wrapper" class="d-flex flex-column">
            <div id="content">
                <?php require 'topbar.php';?>
                <div class="container-fluid">
                    <div class="card shadow mb-4">
                        <div class="card-header py-3">
                            <h5 class="m-0 font-weight-bold text-primary">DATA TEMPLATES</h5>
                        </div>
                        <br>
                        <div class="row ml-4">
                            <button type="button" class="btn btn-success" data-toggle="modal" data-target="#myModalTambah"><i class="fa fa-plus"> Template</i></button>
                        </div>
                        <br>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Area</th>
                                            <th>Process</th>
                                            <th>Item</th>
                                            <th>Point</th>
                                            <th>Unit</th>
                                            <th>Min</th>
                                            <th>Max</th>
                                            <th>Freq</th>
                                            <th>Aksi</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                        $query = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE tanggal IS NULL ORDER BY area, procces");
                                        while ($data = mysqli_fetch_assoc($query)) {
                                        ?>
                                        <tr>
                                            <td><?php echo $data['id']?></td>
                                            <td><?php echo htmlspecialchars($data['area'])?></td>
                                            <td><?php echo htmlspecialchars($data['procces'])?></td>
                                            <td><?php echo htmlspecialchars($data['item'])?></td>
                                            <td><?php echo htmlspecialchars($data['point'])?></td>
                                            <td><?php echo htmlspecialchars($data['unit'])?></td>
                                            <td><?php echo $data['min']?></td>
                                            <td><?php echo $data['max']?></td>
                                            <td><?php echo htmlspecialchars($data['freq'])?></td>
                                            <td>
                                                <a href="#" class="fa fa-edit btn btn-primary btn-sm" data-toggle="modal" data-target="#myModal<?php echo $data['id']; ?>"></a>
                                            </td>
                                        </tr>
                                        <!-- Modal Edit -->
                                        <div class="modal fade" id="myModal<?php echo $data['id']; ?>" role="dialog">
                                            <div class="modal-dialog">
                                                <div class="modal-content">
                                                    <div class="modal-header">
                                                        <h4 class="modal-title">Edit Template</h4>
                                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                                    </div>
                                                    <div class="modal-body">
                                                        <form role="form" action="proses-edit-template.php" method="get">
                                                            <input type="hidden" name="id" value="<?php echo $data['id']; ?>">
                                                            <div class="form-group">
                                                                <label>Area</label>
                                                                <input type="text" name="area" class="form-control" value="<?php echo htmlspecialchars($data['area']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Process</label>
                                                                <input type="text" name="procces" class="form-control" value="<?php echo htmlspecialchars($data['procces']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Item</label>
                                                                <input type="text" name="item" class="form-control" value="<?php echo htmlspecialchars($data['item']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Point</label>
                                                                <input type="text" name="point" class="form-control" value="<?php echo htmlspecialchars($data['point']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Unit</label>
                                                                <input type="text" name="unit" class="form-control" value="<?php echo htmlspecialchars($data['unit']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Min</label>
                                                                <input type="text" name="min" class="form-control" value="<?php echo $data['min']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Max</label>
                                                                <input type="text" name="max" class="form-control" value="<?php echo $data['max']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Freq</label>
                                                                <input type="text" name="freq" class="form-control" value="<?php echo htmlspecialchars($data['freq']); ?>">
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="submit" class="btn btn-success">Ubah</button>
                                                                <a href="hapus-data.php?id=<?=$data['id'];?>&type=template" onclick="return confirm('Anda Yakin Ingin Menghapus?')" class="btn btn-danger">Hapus</a>
                                                                <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                                                            </div>
                                                        </form>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <?php } ?>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal Tambah -->
    <div id="myModalTambah" class="modal fade" role="dialog">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">Tambah Template</h4>
                    <button type="button" class="close" data-dismiss="modal">&times;</button>
                </div>
                <form action="proses-tambah-template.php" method="get">
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Area</label>
                            <input type="text" class="form-control" name="area" required>
                        </div>
                        <div class="form-group">
                            <label>Process</label>
                            <input type="text" class="form-control" name="procces" required>
                        </div>
                        <div class="form-group">
                            <label>Item</label>
                            <input type="text" class="form-control" name="item" required>
                        </div>
                        <div class="form-group">
                            <label>Point</label>
                            <input type="text" class="form-control" name="point" required>
                        </div>
                        <div class="form-group">
                            <label>Unit</label>
                            <input type="text" class="form-control" name="unit" required>
                        </div>
                        <div class="form-group">
                            <label>Min</label>
                            <input type="text" class="form-control" name="min" required>
                        </div>
                        <div class="form-group">
                            <label>Max</label>
                            <input type="text" class="form-control" name="max" required>
                        </div>
                        <div class="form-group">
                            <label>Freq</label>
                            <input type="text" class="form-control" name="freq" required>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-success">Tambah</button>
                        <button type="button" class="btn btn-default" data-dismiss="modal">Keluar</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    <a class="scroll-to-top rounded" href="#page-top"><i class="fas fa-angle-up"></i></a>
    <?php require 'logout-modal.php';?>
    <script src="vendor/jquery/jquery.min.js"></script>
    <script src="vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
    <script src="vendor/jquery-easing/jquery.easing.min.js"></script>
    <script src="js/sb-admin-2.min.js"></script>
    <script src="vendor/datatables/jquery.dataTables.min.js"></script>
    <script src="vendor/datatables/dataTables.bootstrap4.min.js"></script>
    <script>$(document).ready(function(){$('#dataTable').DataTable();});</script>
</body>
</html>
