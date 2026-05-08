<?php
require 'koneksi.php';
require 'cek.php';

$tanggal_filter = isset($_GET['tanggal_filter']) ? $_GET['tanggal_filter'] : '';
if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $tanggal_filter)) {
    $tanggal_filter = '';
}

header("Content-Type: application/vnd.ms-excel");
header("Content-Disposition: attachment; filename=activity_bydate_".($tanggal_filter ?: 'all')."_".date('Ymd_His').".xls");
header("Pragma: no-cache");
header("Expires: 0");

$sql = "
    SELECT point, nilai, unit, remarks, waktu, shift_name FROM (
        SELECT point, shift_satu AS nilai, unit, remarks_satu AS remarks, t_satu AS waktu, 'Shift 1' AS shift_name
        FROM sheetsatu
        WHERE t_satu IS NOT NULL AND shift_satu IS NOT NULL AND shift_satu <> 0

        UNION ALL

        SELECT point, shift_dua AS nilai, unit, remarks_dua AS remarks, t_dua AS waktu, 'Shift 2' AS shift_name
        FROM sheetsatu
        WHERE t_dua IS NOT NULL AND shift_dua IS NOT NULL AND shift_dua <> 0

        UNION ALL

        SELECT point, shift_tiga AS nilai, unit, remarks_tiga AS remarks, t_tiga AS waktu, 'Shift 3' AS shift_name
        FROM sheetsatu
        WHERE t_tiga IS NOT NULL AND shift_tiga IS NOT NULL AND shift_tiga <> 0
    ) AS X
    WHERE 1=1
";

if ($tanggal_filter !== '') {
    $tanggal_safe = mysqli_real_escape_string($koneksi, $tanggal_filter);
    $sql .= " AND DATE(waktu) = '$tanggal_safe' ";
}

$sql .= " ORDER BY waktu ASC";

$q = mysqli_query($koneksi, $sql);

echo "<table border='1'>";
echo "<tr>
        <th>No</th>
        <th>Point</th>
        <th>Shift</th>
        <th>Value</th>
        <th>Unit</th>
        <th>Remarks</th>
        <th>Time</th>
      </tr>";

$no = 1;
while ($row = mysqli_fetch_assoc($q)) {
    $waktu = $row['waktu'] ? date('Y-m-d H:i', strtotime($row['waktu'])) : '';
    echo "<tr>";
    echo "<td>".$no++."</td>";
    echo "<td>".htmlspecialchars($row['point'])."</td>";
    echo "<td>".htmlspecialchars($row['shift_name'])."</td>";
    echo "<td>".htmlspecialchars($row['nilai'])."</td>";
    echo "<td>".htmlspecialchars($row['unit'])."</td>";
    echo "<td>".htmlspecialchars($row['remarks'])."</td>";
    echo "<td>".$waktu."</td>";
    echo "</tr>";
}
echo "</table>";
