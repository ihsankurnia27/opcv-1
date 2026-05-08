<?php
session_start();
require 'koneksi.php';

if (!isset($_SESSION['username'])) {
    http_response_code(401);
    exit('unauthorized');
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('POST only');
}

$username = preg_replace('/[^a-zA-Z0-9_-]/', '', $_SESSION['username']);
$dir = __DIR__ . '/gauge_configs';
if (!is_dir($dir)) {
    mkdir($dir, 0755, true);
}

$input = file_get_contents('php://input');
if ($input === false) {
    http_response_code(400);
    exit('bad request');
}

file_put_contents($dir . '/' . $username . '.json', $input);
header('Content-Type: application/json');
echo json_encode(['saved' => true]);
