<?php
/**
 * Proxy for gauge reader API.
 * Browser JS can't directly call port 8765 from Tailscale/remote.
 * This PHP script relays the detect request server-side.
 */
require 'koneksi.php';
require 'cek.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('POST only');
}

$api_url = getenv('GAUGE_API_URL') ?: 'http://api:8765/detect';

// Forward file + form fields
$postfields = $_POST;
if (isset($_FILES['image'])) {
    $postfields['image'] = new CURLFile(
        $_FILES['image']['tmp_name'],
        $_FILES['image']['type'] ?: 'image/jpeg',
        $_FILES['image']['name'] ?: 'frame.jpg'
    );
}

$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $postfields);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

http_response_code($http_code);
header('Content-Type: application/json');
echo $response;
