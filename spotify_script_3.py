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

# Initialize MFRC522
reader = SimpleMFRC522()

# Define GPIO pins
ENCODER_PIN_A = 15
ENCODER_PIN_B = 14
ENCODER_PIN_AA = 17
ENCODER_PIN_BB = 27
SWITCH_PIN = 4

# Initialize RGB LED
LED_PIN_R = 0
LED_PIN_G = 13
LED_PIN_B = 26
rgb_led = RGBLED(LED_PIN_R, LED_PIN_G, LED_PIN_B)

# Define Rotary Encoders and Button
first_encoder = RotaryEncoder(ENCODER_PIN_A, ENCODER_PIN_B, wrap=False, max_steps=10)
second_encoder = RotaryEncoder(ENCODER_PIN_AA, ENCODER_PIN_BB, wrap=True)
switch = Button(SWITCH_PIN, pull_up=True, bounce_time=.05)

# Define timing constants
DOUBLE_PRESS_TIME = .5  # Time interval to consider as double press
SINGLE_PRESS_DELAY = 1  # Delay to wait for potential second press
QUARTER_TURN_STEPS = 0.5  # Number of steps for a quarter turn of the encoder

# Initialize variables
last_press_time = 0
last_skip_time = time.time()
press_count = 0
presstype = 0
volume_led_timer = None
last_second_encoder_value = 0
current_playlist_index = random.randrange(1, 6, 1)
#current_playlist_index = 0
forward_encoder_count = 0
backward_encoder_count = 0
double_press_flag = 0
last_played_uri = None
sleep_time = 0


# Hardcoded playlists
PLAYLISTS = [
    'playlist:3OW97U4iSQIHFUXMRRh6Us', #Solid Shit 9/16
    'playlist:37i9dQZF1DWXi7h4mmmkzD', #Country Nights
    'playlist:37i9dQZF1DXb8wplbC2YhV', #100 Greates Hip-Hop Songs of the Streaming Era
    'playlist:37i9dQZF1DX0MLFaUdXnjA', #Chill Pop
    'playlist:37i9dQZF1DX17GkScaAekA', #Dark Acadamia Classical
    'playlist:37i9dQZF1DWV7EzJMK2FUI'  #Jazz in the Background
]



# Corresponding colors for the playlists
PLAYLIST_COLORS = [
    (1, 1, 1),  # Red
    (0, 1, 0),  # Green
    (0, 0, 1),  # Blue
    (1, 1, 0),  # Yellow
    (1, 0, 1),  # Magenta
    (0, 1, 1),  # Cyan
]
last_first = first_encoder.value
last_second = second_encoder.value
print(last_first)
print(last_second)

while True:
  if first_encoder.value != last_first:
    print("update volume")
  else:
    print("ignoring volume")
  if second_encoder.value != last_second:
    print("update station")
  else:
    print("ignoring station")
  if button.is_pressed:
    print("toggle pause/play")
    current_playback = sp.current_playback()
    print("current playback is")
    print(current_playback['is_playing'])
  
    if current_playback['is_playing'] == True:
      print("entered pause statement")
      sp.pause_playback(device_id=SPOTIFY_DEVICE_ID)

    elif current_playback['is_playing'] == False:
      print("entered play statement")
      sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
    
  else:
    print("ignore pause/play")
  time.sleep(.25)
