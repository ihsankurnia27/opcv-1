<?php
session_start();
require 'koneksi.php';

if (!isset($_SESSION['username'])) {
    http_response_code(401);
    exit('unauthorized');
}

$username = preg_replace('/[^a-zA-Z0-9_-]/', '', $_SESSION['username']);
$path = __DIR__ . '/gauge_configs/' . $username . '.json';

header('Content-Type: application/json');
if (file_exists($path)) {
    echo file_get_contents($path);
} else {
    echo '{}';
}
