#!/bin/bash

if [ ! -f /var/www/conf/key.txt ]; then
    echo "ERROR: /var/www/conf/key.txt not found" >&2
    exit 1
fi

NEXTCLOUD_SESSIONTOKEN_KEY=$(cat /var/www/conf/key.txt)
if [ -z "$NEXTCLOUD_SESSIONTOKEN_KEY" ]; then
    echo "ERROR: key.txt is empty" >&2
    exit 1
fi

response=$(curl -X POST localhost/apps/sessiontoken/token --silent -d "apikey=$NEXTCLOUD_SESSIONTOKEN_KEY&user=bbb-visio-user&name=app" --write-out "\n%{http_code}")
status_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [[ "$status_code" -ne 200 ]] ; then
    echo "ERROR: Nextcloud sessiontoken API returned $status_code" >&2
    echo "Response body: $body" >&2
    exit 1
else
    exit 0
fi
