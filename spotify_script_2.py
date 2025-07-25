from gpiozero import Button, RotaryEncoder, RGBLED
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import time
import threading
import random
import requests
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

def update_volume():
  try:
    global sleep_time, volume_led_timer
    sleep_time = time.time()
    #try:
    p_encoder_value = first_encoder.value
    new_volume = int(50 + 50 * p_encoder_value)
    sp.volume(new_volume, device_id=SPOTIFY_DEVICE_ID)
    print(f"Volume set to: {new_volume}%")
    volume_level = new_volume / 100
    red_value = 1 - volume_level
    green_value = abs(1 - red_value)
    print(f"Volume Level: {volume_level}%")
    rgb_led.blink(on_time=1, off_time=0.5, on_color=(red_value, green_value, 0), n=1, background=True)
  except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
  except Exception as e:
    print(f"Unexpected error: {e}")

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
 
def update_forward_station():
  global sleep_time, forward_encoder_count, current_playlist_index
  forward_encoder_count = forward_encoder_count + 1
  print(f"Forward encoder count: {forward_encoder_count}")
  seekCount = random.randrange(1, 140000, 1)
  positionCount = random.randrange(1, 20, 1)

  try:
    if forward_encoder_count > 4:
      forward_encoder_count = 1
      current_playlist_index = (current_playlist_index + 1) % len(PLAYLISTS)
      rgb_led.color = PLAYLIST_COLORS[current_playlist_index]
      rgb_led.blink(on_time=1, off_time=0.5,on_color=rgb_led.color, n=1, background=True)
      playlist_id = PLAYLISTS[current_playlist_index]
      print(f"Switching to playlist: {playlist_id}")

      #sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
      sp.start_playback(context_uri=f'spotify:{playlist_id}', offset={"position": positionCount}, position_ms=seekCount, device_id=SPOTIFY_DEVICE_ID)
      sp.shuffle(True)
      #time.sleep(2)
      #sp.start_playback()
      
  except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
  except Exception as e:
    print(f"Unexpected error: {e}")
  

def update_backward_station():
  global sleep_time, backward_encoder_count, current_playlist_index
  sleep_time = time.time()
  backward_encoder_count = backward_encoder_count + 1
  print(f"Backward encoder count: {backward_encoder_count}")
  seekCount = random.randrange(1, 140000, 1)
  positionCount = random.randrange(1, 40, 1)
  try:
    if backward_encoder_count > 4:
      backward_encoder_count = 1
      current_playlist_index = (current_playlist_index - 1) % len(PLAYLISTS)
      rgb_led.color = PLAYLIST_COLORS[current_playlist_index]
      rgb_led.blink(on_time=1, off_time=0.5,on_color=rgb_led.color, n=1, background=True)
      playlist_id = PLAYLISTS[current_playlist_index]
      print(f"Switching to playlist: {playlist_id}")

      #sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
      sp.start_playback(context_uri=f'spotify:{playlist_id}', offset={"position": positionCount}, position_ms=seekCount, device_id=SPOTIFY_DEVICE_ID)
      sp.shuffle(True)
      #time.sleep(2)
      #sp.start_playback()
        
  except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
  except Exception as e:
    print(f"Unexpected error: {e}")
  


def nfc_listener():
  global sleep_time, last_played_uri
  
  try:
    while True:
        print("entered NFC loop")
        print(last_played_uri)
        id, text = reader.read()
        text = text.strip()  # Remove any leading and trailing whitespace
        print(f"NFC tag detected with ID: {id} and text: {text}")
        rgb_led.blink(on_time=1, off_time=0.5, on_color=(1, 1, 0), n=1, background=True)
        current_uri = sp.current_playback()['context']['uri']
        print(current_uri)
        if text == "MFRC_TRIGGER":
          print("entered mapping mode")
          time.sleep(5)
          while True:
            #rgb_led.on(0,0,1)
            rgb_led.blink(on_time=1, off_time=0.5, on_color=(0, 0, 1), background=True)
            id, text = reader.read()
            text = text.strip()
            if text == "MFRC_TRIGGER":
              print("exiting mapping mode")
              rgb_led.off()
              time.sleep(5)
              break
            reader.write(current_uri)
        if text == current_uri or text == last_played_uri:
          print("Current Playing Card")
          continue
        elif text.startswith("spotify:"):
          sleep_time = time.time()
          #sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=False)
          sp.start_playback(context_uri=text, device_id=SPOTIFY_DEVICE_ID)
          time.sleep(2)
          sp.start_playback()
          sp.shuffle(False)
          print(f"Playing Spotify URI: {text}")
          last_played_uri = text
        #else:
        #  print(f"Invalid Spotify URI: {text}")
        #  time.sleep(1)  # Delay between NFC reads
  except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
  except Exception as e:
    print(f"Unexpected error: {e}")

# Attach handlers
first_encoder.when_rotated = update_volume
second_encoder.when_rotated_clockwise = update_forward_station
second_encoder.when_rotated_counter_clockwise = update_backward_station
switch.when_pressed = on_button_press

nfc_thread = threading.Thread(target=nfc_listener)
nfc_thread.daemon = True
nfc_thread.start()

#try:
while True:
  time.sleep(0.01)  # Main loop delay
#except:
  #GPIO.cleanup()
  #rgb_led.off()
  #exit()
  
