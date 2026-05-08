<?php
// run this, then delete
echo 'upload_max_filesize: ' . ini_get('upload_max_filesize') . "\n";
echo 'post_max_size: ' . ini_get('post_max_size') . "\n";
echo 'max_execution_time: ' . ini_get('max_execution_time') . "\n";
echo 'upload_tmp_dir: ' . ini_get('upload_tmp_dir') . "\n";
echo 'open_basedir: ' . ini_get('open_basedir') . "\n";
if (isset($_FILES['test'])) {
    echo 'file error: ' . $_FILES['test']['error'] . "\n";
    echo 'file size: ' . $_FILES['test']['size'] . "\n";
}
