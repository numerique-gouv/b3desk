<?php
$NEXTCLOUD_SESSIONTOKEN_KEY = trim(file_get_contents('../conf/key.txt'), "\r\n");
return array(
    'NC_LOGIN_API_KEY' => $_ENV['NC_LOGIN_API_KEY'],
    'NC_HOST' => $_ENV['NC_HOST'],
    'NEXTCLOUD_SESSIONTOKEN_KEY' => $NEXTCLOUD_SESSIONTOKEN_KEY,
);
?>
