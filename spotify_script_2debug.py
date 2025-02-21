from gpiozero import Button, RotaryEncoder, RGBLED
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import time
import threading
import random
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# Spotify credentials and scope
SPOTIFY_CLIENT_ID = 'c9f4f269f1804bf19f0fefee2539931a'
SPOTIFY_CLIENT_SECRET = 'e5a112f992ee43e9bbea57b8c19b053b'
SPOTIFY_REDIRECT_URI = 'http://10.0.0.217:8080/auth-response/'
SPOTIFY_SCOPE = 'user-modify-playback-state user-read-playback-state'
CACHE_PATH = "/home/diego/spotify_auth_cache2.json"

# Hardcoded Spotify device ID
SPOTIFY_DEVICE_ID = '450e2594318bbcc1e41ca3e88136e118c51a6dcb'

# Initialize Spotipy
sp = Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                       client_secret=SPOTIFY_CLIENT_SECRET,
                                       redirect_uri=SPOTIFY_REDIRECT_URI,
                                       scope=SPOTIFY_SCOPE,
                                       cache_path=CACHE_PATH))

SWITCH_PIN = 4
LED_PIN_R = 0
LED_PIN_G = 13
LED_PIN_B = 26
rgb_led = RGBLED(LED_PIN_R, LED_PIN_G, LED_PIN_B)
switch = Button(SWITCH_PIN, pull_up=True, bounce_time=.05)

def on_button_press():   
  rgb_led.blink(on_time=1, off_time=0.5, on_color=(1, 1, 1), n=1, background=True)
  try:
    current_playback = sp.current_playback()
    if current_playback:
        state = current_playback.get('is_playing', False)
    else:
        state = last_state  # Use last known state if no response

    if state:
        print("entered pause statement")
        sp.pause_playback(device_id=SPOTIFY_DEVICE_ID)
    else:
        print("entered play statement")
        sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)

    last_state = state  # Store state for future reference
  except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
  except Exception as e:
    print(f"Unexpected error: {e}")
    
switch.when_pressed = on_button_press

#try:
while True:
  time.sleep(0.01)  # Main loop delay
#except:
  #GPIO.cleanup()
  #rgb_led.off()
  #exit()
  
