<?php
require 'koneksi.php';
require 'cek.php';

// header supaya browser download sebagai file Excel
header("Content-Type: application/vnd.ms-excel");
header("Content-Disposition: attachment; filename=rekap_aktivitas_10_terbaru.xls");
header("Pragma: no-cache");
header("Expires: 0");

// query sama dengan di rekapdata.php
$sql = "
    SELECT point, shift_satu AS nilai, unit, remarks_satu AS remarks, t_satu AS waktu
    FROM sheetsatu
    WHERE t_satu IS NOT NULL AND shift_satu IS NOT NULL AND shift_satu <> 0
    
    UNION ALL
    
    SELECT point, shift_dua AS nilai, unit, remarks_dua AS remarks, t_dua AS waktu
    FROM sheetsatu
    WHERE t_dua IS NOT NULL AND shift_dua IS NOT NULL AND shift_dua <> 0
    
    UNION ALL
    
    SELECT point, shift_tiga AS nilai, unit, remarks_tiga AS remarks, t_tiga AS waktu
    FROM sheetsatu
    WHERE t_tiga IS NOT NULL AND shift_tiga IS NOT NULL AND shift_tiga <> 0
    
    ORDER BY waktu DESC
    LIMIT 10
";

$query = mysqli_query($koneksi, $sql);

// mulai output tabel HTML (Excel bisa baca format ini)
echo "<table border='1'>";
echo "
<tr>
    <th>No</th>
    <th>Point</th>
    <th>Value</th>
    <th>Unit</th>
    <th>Remarks</th>
    <th>Time</th>
</tr>
";

$no = 1;
while ($row = mysqli_fetch_assoc($query)) {
    $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';

    echo "<tr>";
    echo "<td>".$no++."</td>";
    echo "<td>".$row['point']."</td>";
    echo "<td>".$row['nilai']."</td>";
    echo "<td>".$row['unit']."</td>";
    echo "<td>".$row['remarks']."</td>";
    echo "<td>".$waktu."</td>";
    echo "</tr>";
}

echo "</table>";
