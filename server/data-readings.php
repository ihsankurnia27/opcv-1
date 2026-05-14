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
    <title>Data Readings</title>
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
                            <h5 class="m-0 font-weight-bold text-primary">DATA READINGS</h5>
                        </div>
                        <br>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Area</th>
                                            <th>Item</th>
                                            <th>Point</th>
                                            <th>Tanggal</th>
                                            <th>Shift 1</th>
                                            <th>Remarks 1</th>
                                            <th>Shift 2</th>
                                            <th>Remarks 2</th>
                                            <th>Shift 3</th>
                                            <th>Remarks 3</th>
                                            <th>Aksi</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <?php
                                        $query = mysqli_query($koneksi, "SELECT * FROM sheetsatu WHERE tanggal IS NOT NULL ORDER BY tanggal DESC, area");
                                        while ($data = mysqli_fetch_assoc($query)) {
                                        ?>
                                        <tr>
                                            <td><?php echo $data['id']?></td>
                                            <td><?php echo htmlspecialchars($data['area'])?></td>
                                            <td><?php echo htmlspecialchars($data['item'])?></td>
                                            <td><?php echo htmlspecialchars($data['point'])?></td>
                                            <td><?php echo $data['tanggal']?></td>
                                            <td><?php echo $data['shift_satu']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_satu'])?></td>
                                            <td><?php echo $data['shift_dua']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_dua'])?></td>
                                            <td><?php echo $data['shift_tiga']?></td>
                                            <td><?php echo htmlspecialchars($data['remarks_tiga'])?></td>
                                            <td>
                                                <a href="#" class="fa fa-edit btn btn-primary btn-sm" data-toggle="modal" data-target="#myModal<?php echo $data['id']; ?>"></a>
                                            </td>
                                        </tr>
                                        <!-- Modal Edit -->
                                        <div class="modal fade" id="myModal<?php echo $data['id']; ?>" role="dialog">
                                            <div class="modal-dialog">
                                                <div class="modal-content">
                                                    <div class="modal-header">
                                                        <h4 class="modal-title">Edit Reading</h4>
                                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                                    </div>
                                                    <div class="modal-body">
                                                        <form role="form" action="proses-edit-reading.php" method="get">
                                                            <input type="hidden" name="id" value="<?php echo $data['id']; ?>">
                                                            <div class="form-group">
                                                                <label>Area</label>
                                                                <input type="text" class="form-control" value="<?php echo htmlspecialchars($data['area']); ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Point</label>
                                                                <input type="text" class="form-control" value="<?php echo htmlspecialchars($data['point']); ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Tanggal</label>
                                                                <input type="text" class="form-control" value="<?php echo $data['tanggal']; ?>" readonly>
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 1</label>
                                                                <input type="text" name="shift_satu" class="form-control" value="<?php echo $data['shift_satu']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 1</label>
                                                                <input type="text" name="remarks_satu" class="form-control" value="<?php echo htmlspecialchars($data['remarks_satu']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 2</label>
                                                                <input type="text" name="shift_dua" class="form-control" value="<?php echo $data['shift_dua']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 2</label>
                                                                <input type="text" name="remarks_dua" class="form-control" value="<?php echo htmlspecialchars($data['remarks_dua']); ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Shift 3</label>
                                                                <input type="text" name="shift_tiga" class="form-control" value="<?php echo $data['shift_tiga']; ?>">
                                                            </div>
                                                            <div class="form-group">
                                                                <label>Remarks 3</label>
                                                                <input type="text" name="remarks_tiga" class="form-control" value="<?php echo htmlspecialchars($data['remarks_tiga']); ?>">
                                                            </div>
                                                            <div class="modal-footer">
                                                                <button type="submit" class="btn btn-success">Ubah</button>
                                                                <a href="hapus-data.php?id=<?=$data['id'];?>&type=reading" onclick="return confirm('Anda Yakin Ingin Menghapus?')" class="btn btn-danger">Hapus</a>
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
