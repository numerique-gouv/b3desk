
#!/bin/bash

status_code=$(curl -X POST localhost/apps/sessiontoken/token --silent --output /dev/null -d "apikey=$NEXTCLOUD_SESSIONTOKEN_KEY&user=bbb-visio-user&name=app" --write-out %{http_code})

if [[ "$status_code" -ne 200 ]] ; then
    exit 1
else
    exit 0
fi
