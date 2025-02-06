#!/bin/bash

SERVICE_NAME="dylan_spotify.service"
TEST_URL="https://api.spotify.com/v1"
LOG_FILE="/var/log/watchdog.log"

while true; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL")

    if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "401" ]]; then
        echo "$(date): Connection to $TEST_URL is healthy (HTTP $HTTP_STATUS)." | tee -a "$LOG_FILE"
    else
        echo "$(date): Connection to $TEST_URL failed (HTTP $HTTP_STATUS). Restarting $SERVICE_NAME..." | tee -a "$LOG_FILE"
        systemctl restart "$SERVICE_NAME"
    fi

    sleep 30  # Check every 30 seconds
done
