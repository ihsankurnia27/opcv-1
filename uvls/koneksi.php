<?php
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_user = getenv('DB_USER') ?: 'root';
$db_pass = getenv('DB_PASS') ?: 'uvls123';
$db_name = getenv('DB_NAME') ?: 'ua1-1';

$koneksi = mysqli_connect($db_host, $db_user, $db_pass, $db_name);
?>