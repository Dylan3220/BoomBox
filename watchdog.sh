#!/bin/bash

SERVICE_NAME="dylan_spotify.service"
TEST_URL="https://api.spotify.com/v1"  # Replace with the URL your application depends on
LOG_FILE="/var/log/watchdog.log"

while true; do
    # Try to connect to the Spotify API (or relevant service)
    if ! curl -s --head --request GET "$TEST_URL" | grep "200 OK" > /dev/null; then
        echo "$(date): Connection to $TEST_URL failed. Restarting $SERVICE_NAME..." | tee -a "$LOG_FILE"
        systemctl restart "$SERVICE_NAME"
    else
        echo "$(date): Connection to $TEST_URL is healthy." | tee -a "$LOG_FILE"
    fi
    sleep 30  # Check every 30 seconds
done
