#!/bin/bash
sudo wget -O /home/diego/spotify_script_2.py https://raw.githubusercontent.com/Dylan3220/BoomBox/main/spotify_script_2.py
sudo wget -O /etc/systemd/system/dylan_spotify.service https://raw.githubusercontent.com/Dylan3220/BoomBox/main/dylan_spotify.service 
sudo wget -O /etc/systemd/system/watchdog.service https://raw.githubusercontent.com/Dylan3220/BoomBox/main/watchdog.service
sudo wget -O /home/diego/watchdog.sh https://raw.githubusercontent.com/Dylan3220/BoomBox/main/watchdog.sh
sudo wget -O /boot/firmware/config.txt https://raw.githubusercontent.com/Dylan3220/BoomBox/main/config.txt
sudo apt-get -y install curl && curl -sL https://dtcooper.github.io/raspotify/install.sh | sh  
sudo apt install python3-pip
pip install spotipy --break-system-packages 
pip install mfrc522 --break-system-packages

sudo systemctl enable dylan_spotify.service
sudo systemctl enable watchdog.service
sudo systemctl daemon-reload
