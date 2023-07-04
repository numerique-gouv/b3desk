
#!/bin/bash

token=$(curl -X POST -H "X-API-KEY: $NC_LOGIN_API_KEY" -H "Content-Type: application/json" -d '{"username":"bbb-visio-user"}' http://localhost/index.php)

if echo $token | grep -v -e "\"nctoken\":null" -e "Denied"
then
    exit 0
else
    exit 1
fi
