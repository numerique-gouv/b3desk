<?php

// this code will requests :

// curl -XPOST https://nextcloud.instance.com/apps/sessiontoken/token -d "apikey=ffffffffffffff&user=admin&name=tokenmock"
// answers :
// {"token":"aaa-aaa-aaa-aaa","loginName":"admin","deviceToken":{"id":3,"name":"tokenmock","lastActivity":1677754112,"type":1,"scope":{"filesystem":true}}}

// this code should answer in format :
// return {"nctoken": None, "nclocator": None, "nclogin": None}

$config=include('./config.php');

$NC_LOGIN_API_KEY=$config['NC_LOGIN_API_KEY'];
$NEXTCLOUD_SESSIONTOKEN_ENDPOINT=$config['NC_HOST'].'/apps/sessiontoken/token';
$NEXTCLOUD_SESSIONTOKEN_KEY=$config['NEXTCLOUD_SESSIONTOKEN_KEY'];

$data = json_decode(file_get_contents('php://input'), true);

$LOGIN=$data['username'];

if (isset($_SERVER["HTTP_X_API_KEY"]) && $_SERVER["HTTP_X_API_KEY"]==$NC_LOGIN_API_KEY) {
    header("Content-Type: application/json");


    // Create a new cURL resource
    $ch = curl_init($NEXTCLOUD_SESSIONTOKEN_ENDPOINT);


    curl_setopt($ch, CURLOPT_URL, $NEXTCLOUD_SESSIONTOKEN_ENDPOINT);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, "apikey=".$NEXTCLOUD_SESSIONTOKEN_KEY."&name=tokenmock&user=".$LOGIN);

    // Return response instead of outputting
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    // Execute the POST request
    $result = curl_exec($ch);

    // Close cURL resource
    curl_close($ch);

    $nc_data=json_decode($result, True);

    $nc_data_to_answer = array();
    $nc_data_to_answer['nctoken'] = $nc_data['token'];
    $nc_data_to_answer['nclocator'] = $config['NC_HOST'];
    $nc_data_to_answer['nclogin'] = $LOGIN;

    header("Content-Type: application/json");
    echo json_encode($nc_data_to_answer);

} else {
    header("HTTP/1.0 403 Denied");
    echo "Denied";
    exit();
}
