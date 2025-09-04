#!/usr/bin/env python3
import time
import threading
import random
from gpiozero import Button, RotaryEncoder, RGBLED
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import requests

# -----------------------
# CONFIG
# -----------------------
SPOTIFY_CLIENT_ID = 'c9f4f269f1804bf19f0fefee2539931a'
SPOTIFY_CLIENT_SECRET = 'e5a112f992ee43e9bbea57b8c19b053b'
SPOTIFY_REDIRECT_URI = 'http://10.0.0.217:8080/auth-response/'
SPOTIFY_SCOPE = 'user-modify-playback-state user-read-playback-state'
CACHE_PATH = "/home/diego/spotify_auth_cache2.json"
SPOTIFY_DEVICE_ID = '450e2594318bbcc1e41ca3e88136e118c51a6dcb'

ENCODER_PIN_A = 15
ENCODER_PIN_B = 14
ENCODER_PIN_AA = 17
ENCODER_PIN_BB = 27
SWITCH_PIN = 4

LED_PIN_R = 0
LED_PIN_G = 13
LED_PIN_B = 26

PLAYLISTS = [
    'spotify:playlist:3OW97U4iSQIHFUXMRRh6Us',
    'spotify:playlist:37i9dQZF1DWXi7h4mmmkzD',
    'spotify:playlist:37i9dQZF1DXb8wplbC2YhV',
    'spotify:playlist:37i9dQZF1DX0MLFaUdXnjA',
    'spotify:playlist:37i9dQZF1DX17GkScaAekA',
    'spotify:playlist:37i9dQZF1DWV7EzJMK2FUI'
]

PLAYLIST_COLORS = [
    (1, 1, 1), (0, 1, 0), (0, 0, 1),
    (1, 1, 0), (1, 0, 1), (0, 1, 1)
]

LED_ON_TIME = 0.5  # seconds to keep LED on after action

# -----------------------
# SETUP
# -----------------------
GPIO.setwarnings(False)
reader = SimpleMFRC522()
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path=CACHE_PATH
))

rgb_led = RGBLED(LED_PIN_R, LED_PIN_G, LED_PIN_B)
first_encoder = RotaryEncoder(ENCODER_PIN_A, ENCODER_PIN_B, wrap=False, max_steps=10)
second_encoder = RotaryEncoder(ENCODER_PIN_AA, ENCODER_PIN_BB, wrap=True)
switch = Button(SWITCH_PIN, pull_up=True, bounce_time=.05)

# -----------------------
# STATE
# -----------------------
last_state = False
last_played_uri = None
forward_encoder_count = 0
backward_encoder_count = 0
current_playlist_index = random.randrange(0, len(PLAYLISTS))

# -----------------------
# SPOTIFY HELPER
# -----------------------
def spotify_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def led_feedback(color):
    """Turn LED on and leave it on for a short period"""
    rgb_led.color = color
    threading.Timer(LED_ON_TIME, lambda: rgb_led.off()).start()

# -----------------------
# HANDLERS
# -----------------------
def update_volume():
    try:
        p_encoder_value = first_encoder.value
        new_volume = int(50 + 50 * p_encoder_value)
        new_volume = max(0, min(100, new_volume))
        spotify_call(sp.volume, new_volume, device_id=SPOTIFY_DEVICE_ID)
        red_value = 1 - new_volume / 100
        green_value = new_volume / 100
        led_feedback((red_value, green_value, 0))
        print(f"Volume set to: {new_volume}%")
    except Exception as e:
        print(f"Volume error: {e}")

def on_button_press():
    global last_state
    try:
        playback = spotify_call(sp.current_playback)
        if playback:
            is_playing = playback.get('is_playing', False)
            device = playback.get('device', {}).get('id', None)
        else:
            is_playing = last_state
            device = SPOTIFY_DEVICE_ID

        if is_playing:
            print("Pausing playback")
            spotify_call(sp.pause_playback, device_id=SPOTIFY_DEVICE_ID)
            led_feedback((1, 1, 1))
            last_state = False
        else:
            if device == SPOTIFY_DEVICE_ID:
                print("Resuming playback on Pi")
                spotify_call(sp.start_playback, device_id=SPOTIFY_DEVICE_ID)
            else:
                print("Transferring playback to Pi and playing")
                spotify_call(sp.transfer_playback, device_id=SPOTIFY_DEVICE_ID, force_play=True)
            led_feedback((1, 1, 1))
            last_state = True
    except Exception as e:
        print(f"Pause/resume error: {e}")

def play_random_track_in_playlist(playlist_uri):
    try:
        offset = {"position": random.randint(0, 20)}
        position_ms = random.randint(0, 140000)
        spotify_call(sp.start_playback, context_uri=playlist_uri,
                     offset=offset, position_ms=position_ms,
                     device_id=SPOTIFY_DEVICE_ID)
        time.sleep(0.1)
        spotify_call(sp.shuffle, True, device_id=SPOTIFY_DEVICE_ID)
    except Exception as e:
        print(f"Random track play error: {e}")

def update_forward_station():
    global forward_encoder_count, current_playlist_index
    forward_encoder_count += 1
    if forward_encoder_count > 4:
        forward_encoder_count = 1
        current_playlist_index = (current_playlist_index + 1) % len(PLAYLISTS)
        playlist_id = PLAYLISTS[current_playlist_index]
        led_feedback(PLAYLIST_COLORS[current_playlist_index])
        play_random_track_in_playlist(playlist_id)
        print(f"Switching to playlist: {playlist_id}")

def update_backward_station():
    global backward_encoder_count, current_playlist_index
    backward_encoder_count += 1
    if backward_encoder_count > 4:
        backward_encoder_count = 1
        current_playlist_index = (current_playlist_index - 1) % len(PLAYLISTS)
        playlist_id = PLAYLISTS[current_playlist_index]
        led_feedback(PLAYLIST_COLORS[current_playlist_index])
        play_random_track_in_playlist(playlist_id)
        print(f"Switching to playlist: {playlist_id}")

# -----------------------
# NFC THREAD
# -----------------------
def nfc_listener():
    global last_played_uri
    last_card_id = None
    card_present = False

    while True:
        try:
            id, text = reader.read()
            text = (text or "").strip()
            
            if not text:
                last_card_id = None
                card_present = False
                time.sleep(0.05)
                continue

            if id == last_card_id and card_present:
                time.sleep(0.2)
                continue

            last_card_id = id
            card_present = True
            led_feedback((1, 1, 0))
            print(f"NFC card detected: {id}, {text}")

            if text == "MFRC_TRIGGER":
                print("Mapping mode activated")
                while True:
                    id2, text2 = reader.read()
                    text2 = (text2 or "").strip()
                    if text2 == "MFRC_TRIGGER":
                        print("Mapping mode exit")
                        rgb_led.off()
                        break
                    if last_played_uri:
                        print(f"Writing {last_played_uri} to card")
                        reader.write(last_played_uri)
            elif text.startswith("spotify:album:") or \
                 text.startswith("spotify:track:") or \
                 text.startswith("spotify:playlist:"):
                if text != last_played_uri:
                    print(f"Playing URI from card: {text}")
                    try:
                        spotify_call(sp.start_playback, context_uri=text, device_id=SPOTIFY_DEVICE_ID)
                        time.sleep(0.1)
                        spotify_call(sp.shuffle, False, device_id=SPOTIFY_DEVICE_ID)
                        last_played_uri = text
                    except Exception as e:
                        print(f"Spotify playback error: {e}")
        except Exception as e:
            if "AUTH ERROR" in str(e) or "Error while reading" in str(e):
                time.sleep(0.2)
            else:
                print(f"NFC listener unexpected error: {e}")
        time.sleep(0.05)

# -----------------------
# ATTACH CALLBACKS
# -----------------------
first_encoder.when_rotated = update_volume
second_encoder.when_rotated_clockwise = update_forward_station
second_encoder.when_rotated_counter_clockwise = update_backward_station
switch.when_pressed = on_button_press

nfc_thread = threading.Thread(target=nfc_listener, daemon=True)
nfc_thread.start()

# -----------------------
# MAIN LOOP
# -----------------------
print("Running... Ctrl+C to exit.")
try:
    while True:
        time.sleep(0.01)
except KeyboardInterrupt:
    GPIO.cleanup()
    rgb_led.off()
    print("Exiting...")
