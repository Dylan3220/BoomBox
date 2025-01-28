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
current_playlist_index = 0
forward_encoder_count = 0
backward_encoder_count = 0
double_press_flag = 0
last_played_uri = None


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
    (1, 0, 0),  # Red
    (0, 1, 0),  # Green
    (0, 0, 1),  # Blue
    (1, 1, 0),  # Yellow
    (1, 0, 1),  # Magenta
    (0, 1, 1),  # Cyan
]

def update_volume():
    global volume_led_timer
    #try:
    p_encoder_value = first_encoder.value
    new_volume = int(50 + 50 * p_encoder_value)
    sp.volume(new_volume, device_id=SPOTIFY_DEVICE_ID)
    print(f"Volume set to: {new_volume}%")
    volume_level = new_volume / 100
    rgb_led.blink(on_time=1, off_time=0.5, on_color=(0, 0, volume_level), n=3, background=True)

 #   except:
 #     exit()

    #if volume_led_timer:
    #    volume_led_timer.cancel()
    #volume_level = new_volume / 100
    #rgb_led.blink(on_time=1, off_time=0.5, on_color=(0, 0, volume_level), n=3, background=True)
    #volume_led_timer = threading.Timer(3, rgb_led.off())
    #volume_led_timer.start()


def on_button_press():   

    global last_press_time, last_skip_time, press_count, double_press_flag
    rgb_led.blink(on_time=1, off_time=0.5, on_color=(1, 0, 1), n=3, background=True)

    
    try:
      current_playback = sp.current_playback()
      
      print("current playback is")
      print(current_playback['is_playing'])
    
      if current_playback['is_playing'] == True:
        print("entered pause statement")
        sp.pause_playback(device_id=SPOTIFY_DEVICE_ID)
  
      elif current_playback['is_playing'] == False:
        print("entered play statement")
        sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=False)
        sp.start_playback(device_id=SPOTIFY_DEVICE_ID)
        
    except:
      print("entered pause/play except statement")
      sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=False)
      sp.start_playback(device_id=SPOTIFY_DEVICE_ID)
      #exit()
  
    """last_press_time = time.time()
    print("entered button function")

    while (time.time() - last_press_time < DOUBLE_PRESS_TIME):
        print("im in the while loop")
        print(double_press_flag)
        print (time.time() - last_press_time)
        #time.time() = time.time()
        time.sleep(.125)
        double_press_flag = 1
        if switch.is_pressed:
            #rgb_led.on()
            print("Button Double Pressed: Skipping Song")
            sp.next_track(device_id=SPOTIFY_DEVICE_ID)
            sp.start_playback(device_id=SPOTIFY_DEVICE_ID)
            last_skip_time = time.time()
            #rgb_led.off()
            double_press_flag = 0
            break 

    if double_press_flag and last_press_time - last_skip_time > 5:
        print("Button Single Pressed: Toggle Pause/Play")
        #current_playback = sp.current_playback()
        if current_playback and current_playback['is_playing']:
            sp.pause_playback(device_id=SPOTIFY_DEVICE_ID)
        else:
            sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)  
    double_press_flag = 0"""
    


 
def update_forward_station():
    global forward_encoder_count, current_playlist_index
    forward_encoder_count = forward_encoder_count + 1
    print(f"Forward encoder count: {forward_encoder_count}")
    seekCount = random.randrange(1, 140000, 1)
    positionCount = random.randrange(1, 20, 1)

    try:
      if forward_encoder_count > 4:
        forward_encoder_count = 1
        rgb_led.blink(on_time=1, off_time=0.5, on_color=(0, 1, 0), n=3, background=True)
        current_playlist_index = (current_playlist_index + 1) % len(PLAYLISTS)
        playlist_id = PLAYLISTS[current_playlist_index]
  
        print(f"Switching to playlist: {playlist_id}")
  
        sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
        sp.start_playback(context_uri=f'spotify:{playlist_id}', offset={"position": positionCount}, position_ms=seekCount, device_id=SPOTIFY_DEVICE_ID)
        time.sleep(2)
        sp.start_playback()
        
    except:
      exit()
        #rgb_led.color = PLAYLIST_COLORS[current_playlist_index]

def update_backward_station():
    global backward_encoder_count, current_playlist_index
    backward_encoder_count = backward_encoder_count + 1
    print(f"Backward encoder count: {backward_encoder_count}")
    seekCount = random.randrange(1, 140000, 1)
    positionCount = random.randrange(1, 20, 1)
    try:
      if backward_encoder_count > 4:
        backward_encoder_count = 1
        rgb_led.blink(on_time=1, off_time=0.5, on_color=(1, 0, 0), n=3, background=True)
        current_playlist_index = (current_playlist_index - 1) % len(PLAYLISTS)
        playlist_id = PLAYLISTS[current_playlist_index]

        print(f"Switching to playlist: {playlist_id}")

        sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
        sp.start_playback(context_uri=f'spotify:{playlist_id}', offset={"position": positionCount}, position_ms=seekCount, device_id=SPOTIFY_DEVICE_ID)
        time.sleep(2)
        sp.start_playback()
        
    except:
      exit()
        #rgb_led.color = PLAYLIST_COLORS[current_playlist_index]

def monitor_playback():
  global current_playback
  while True:
    try:
      current_playback = sp.current_playback()
      print(current_playback['is_playing'])
      time.sleep(1)  # Check playback status every second
    except:
      print("error in monitor playback")
      continue

def nfc_listener():
    global last_played_uri
    
    try:
      while True:
          print("entered NFC loop")
          print(last_played_uri)
          id, text = reader.read()
          text = text.strip()  # Remove any leading and trailing whitespace
          print(f"NFC tag detected with ID: {id} and text: {text}")
          rgb_led.blink(on_time=1, off_time=0.5, on_color=(1, 1, 0), n=3, background=True)
          current_uri = sp.current_playback()['context']['uri']
          print(current_uri)
          if text == "MFRC_TRIGGER":
            time.sleep(5)
            while True:
              #rgb_led.on(0,0,1)
              print("entered mapping mode")
              id, text = reader.read()
              text = text.strip()
              if text == "MFRC_TRIGGER":
                print("exiting mapping mode")
                time.sleep(5)
                break
              reader.write(current_uri)
          if text == current_uri or text == last_played_uri:
            print("Current Playing Card")
            continue
          elif text.startswith("spotify:"):
            sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=False)
            sp.start_playback(context_uri=text, device_id=SPOTIFY_DEVICE_ID)
            time.sleep(2)
            sp.start_playback()
            print(f"Playing Spotify URI: {text}")
            last_played_uri = text
          #else:
          #  print(f"Invalid Spotify URI: {text}")
          #  time.sleep(1)  # Delay between NFC reads
    except:
      exit()
    
# Attach handlers
first_encoder.when_rotated = update_volume
second_encoder.when_rotated_clockwise = update_forward_station
second_encoder.when_rotated_counter_clockwise = update_backward_station
switch.when_pressed = on_button_press

#playback_thread = threading.Thread(target=monitor_playback)
#playback_thread.daemon = True
#playback_thread.start()

nfc_thread = threading.Thread(target=nfc_listener)
nfc_thread.daemon = True
nfc_thread.start()

while True:
    time.sleep(0.01)  # Main loop delay
