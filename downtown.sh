#!/bin/bash
sudo wget -O /home/diego/spotify_script_2.py https://raw.githubusercontent.com/Dylan3220/BoomBox/main/spotify_script_2.py
sudo wget -O /etc/systemd/system/dylan_spotify.service https://raw.githubusercontent.com/Dylan3220/BoomBox/main/dylan_spotify.service 

##sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable dylan_spotify.service
sudo systemctl start dylan_spotify.service
