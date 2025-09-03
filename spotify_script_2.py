#!/usr/bin/env python3
import time
import threading
import random
import requests

from gpiozero import Button, RotaryEncoder, RGBLED
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# -----------------------
# CONFIG (use your values)
# -----------------------
SPOTIFY_CLIENT_ID = 'c9f4f269f1804bf19f0fefee2539931a'
SPOTIFY_CLIENT_SECRET = 'e5a112f992ee43e9bbea57b8c19b053b'
SPOTIFY_REDIRECT_URI = 'http://10.0.0.217:8080/auth-response/'
SPOTIFY_SCOPE = 'user-modify-playback-state user-read-playback-state'
CACHE_PATH = "/home/diego/spotify_auth_cache2.json"
SPOTIFY_DEVICE_ID = '450e2594318bbcc1e41ca3e88136e118c51a6dcb'

# GPIO pins (your original values)
ENCODER_PIN_A = 15
ENCODER_PIN_B = 14
ENCODER_PIN_AA = 17
ENCODER_PIN_BB = 27
SWITCH_PIN = 4

LED_PIN_R = 0
LED_PIN_G = 13
LED_PIN_B = 26

# Playlists and colors (from your earlier list)
PLAYLISTS = [
    'playlist:3OW97U4iSQIHFUXMRRh6Us', #Solid Shit 9/16
    'playlist:37i9dQZF1DWXi7h4mmmkzD', #Country Nights
    'playlist:37i9dQZF1DXb8wplbC2YhV', #Hip-Hop list
    'playlist:37i9dQZF1DX0MLFaUdXnjA', #Chill Pop
    'playlist:37i9dQZF1DX17GkScaAekA', #Dark Academia Classical
    'playlist:37i9dQZF1DWV7EzJMK2FUI'  #Jazz
]

PLAYLIST_COLORS = [
    (1, 1, 1),
    (0, 1, 0),
    (0, 0, 1),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 1),
]

# -----------------------
# SETUP
# -----------------------
GPIO.setwarnings(False)  # suppress MFRC522 "channel already in use" warning spam
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
# State
# -----------------------
last_state = False
last_played_uri = None
sleep_time = 0
forward_encoder_count = 0
backward_encoder_count = 0
current_playlist_index = random.randrange(0, len(PLAYLISTS))
volume_led_timer = None

# -----------------------
# Helper: normalize URI
# -----------------------
def normalize_uri(uri):
    """Return a spotify:... context URI. Accepts 'playlist:...' or 'spotify:playlist:...'."""
    if not uri:
        return uri
    if uri.startswith('spotify:'):
        return uri
    if uri.startswith('playlist:') or uri.startswith('album:') or uri.startswith('track:'):
        return 'spotify:' + uri
    # if the user passed an http URL or something else, leave it as-is
    return uri

# -----------------------
# Spotify wrapper
# -----------------------
def spotify_call(func, *args, **kwargs):
    """
    Call a Spotipy function. If Spotify returns a "no active device" (404),
    force transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True),
    wait a short moment, and retry once.
    Returns the function result or None on unrecoverable error.
    """
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except SpotifyException as e:
            msg = str(e)
            status = getattr(e, "http_status", None)
            # detect No active device situation
            if status == 404 or "no active device" in msg.lower() or "NO_ACTIVE_DEVICE" in msg.upper():
                print("⚠️ Spotify: No active device. Forcing playback to our device (force_play=True)...")
                try:
                    sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
                except Exception as te:
                    print(f"Error while transfer_playback: {te}")
                time.sleep(0.6)  # let Spotify register the device switch
                continue
            # token/auth problems
            if status == 401:
                print("⚠️ Spotify: 401 Unauthorized - token may be expired.")
                # spotipy's OAuth manager normally refreshes automatically on next call,
                # so we just wait a bit and retry.
                time.sleep(0.5)
                continue
            print(f"SpotifyException ({status}): {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Network error during Spotify call: {e}. Retrying...")
            time.sleep(0.5)
            continue
        except Exception as e:
            print(f"Unexpected error during Spotify call: {e}")
            return None
    print("spotify_call: attempts exhausted, returning None.")
    return None

# -----------------------
# Spotify helper functions
# -----------------------
def set_volume(vol):
    spotify_call(sp.volume, vol, device_id=SPOTIFY_DEVICE_ID)

def toggle_shuffle(state):
    spotify_call(sp.shuffle, state, device_id=SPOTIFY_DEVICE_ID)

def start_playback_uri(uri, offset_position=None, position_ms=None):
    ctx = normalize_uri(uri)
    kwargs = {"device_id": SPOTIFY_DEVICE_ID}
    if offset_position is not None:
        kwargs["offset"] = {"position": offset_position}
    if position_ms is not None:
        kwargs["position_ms"] = position_ms
    spotify_call(sp.start_playback, context_uri=ctx, **kwargs)

def pause_playback():
    spotify_call(sp.pause_playback, device_id=SPOTIFY_DEVICE_ID)

def transfer_and_play():
    spotify_call(sp.transfer_playback, device_id=SPOTIFY_DEVICE_ID, force_play=True)

# -----------------------
# Handlers
# -----------------------
def update_volume():
    global sleep_time
    try:
        sleep_time = time.time()
        p_encoder_value = first_encoder.value
        # map encoder value to 0..100 (adjust formula to taste)
        new_volume = int(50 + 50 * p_encoder_value)
        new_volume = max(0, min(100, new_volume))
        set_volume(new_volume)
        print(f"Volume set to: {new_volume}%")
        volume_level = new_volume / 100
        red_value = 1 - volume_level
        green_value = abs(1 - red_value)
        rgb_led.blink(on_time=0.3, off_time=0.2, on_color=(red_value, green_value, 0), n=1, background=True)
    except Exception as e:
        print(f"Unexpected error in update_volume: {e}")

def on_button_press():
    global last_state
    rgb_led.blink(on_time=0.3, off_time=0.2, on_color=(1, 1, 1), n=1, background=True)
    try:
        playback = spotify_call(sp.current_playback)
        if playback:
            state = playback.get('is_playing', False)
        else:
            state = last_state
        if state:
            print("Pausing playback.")
            pause_playback()
            last_state = False
        else:
            print("Resuming/transfer playback to device.")
            # Ensure device active and start playback
            transfer_and_play()
            last_state = True
    except Exception as e:
        print(f"Unexpected error in on_button_press: {e}")

def update_forward_station():
    global sleep_time, forward_encoder_count, current_playlist_index
    forward_encoder_count += 1
    print(f"Forward encoder count: {forward_encoder_count}")
    seekCount = random.randrange(1, 140000, 1)
    positionCount = random.randrange(1, 20, 1)
    try:
        if forward_encoder_count > 4:
            forward_encoder_count = 1
            current_playlist_index = (current_playlist_index + 1) % len(PLAYLISTS)
            rgb_led.color = PLAYLIST_COLORS[current_playlist_index]
            rgb_led.blink(on_time=0.5, off_time=0.25, on_color=rgb_led.color, n=1, background=True)
            playlist_id = PLAYLISTS[current_playlist_index]
            print(f"Switching to playlist: {playlist_id}")
            start_playback_uri(playlist_id, offset_position=positionCount, position_ms=seekCount)
            toggle_shuffle(True)
    except Exception as e:
        print(f"Unexpected error in update_forward_station: {e}")

def update_backward_station():
    global sleep_time, backward_encoder_count, current_playlist_index
    backward_encoder_count += 1
    print(f"Backward encoder count: {backward_encoder_count}")
    seekCount = random.randrange(1, 140000, 1)
    positionCount = random.randrange(1, 40, 1)
    try:
        if backward_encoder_count > 4:
            backward_encoder_count = 1
            current_playlist_index = (current_playlist_index - 1) % len(PLAYLISTS)
            rgb_led.color = PLAYLIST_COLORS[current_playlist_index]
            rgb_led.blink(on_time=0.5, off_time=0.25, on_color=rgb_led.color, n=1, background=True)
            playlist_id = PLAYLISTS[current_playlist_index]
            print(f"Switching to playlist: {playlist_id}")
            start_playback_uri(playlist_id, offset_position=positionCount, position_ms=seekCount)
            toggle_shuffle(True)
    except Exception as e:
        print(f"Unexpected error in update_backward_station: {e}")

# -----------------------
# NFC listener thread
# -----------------------
def nfc_listener():
    global sleep_time, last_played_uri
    try:
        while True:
            try:
                print("entered NFC loop")
                id, text = reader.read()
                text = (text or "").strip()
                print(f"NFC tag detected: id={id}, text='{text}'")
                rgb_led.blink(on_time=0.4, off_time=0.2, on_color=(1,1,0), n=1, background=True)
                playback = spotify_call(sp.current_playback)
                current_uri = None
                if playback and playback.get('context'):
                    current_uri = playback['context'].get('uri')
                # mapping mode activation tag
                if text == "MFRC_TRIGGER":
                    print("entered mapping mode (press another card to map current URI)")
                    time.sleep(2)
                    while True:
                        rgb_led.blink(on_time=0.4, off_time=0.2, on_color=(0,0,1), background=True)
                        id2, text2 = reader.read()
                        text2 = (text2 or "").strip()
                        if text2 == "MFRC_TRIGGER":
                            print("exiting mapping mode")
                            rgb_led.off()
                            time.sleep(0.5)
                            break
                        # write current URI to tag (useful only if current_uri exists)
                        if current_uri:
                            print(f"Writing '{current_uri}' to tag.")
                            reader.write(current_uri)
                        else:
                            print("No current context to map onto tag.")
                elif text:
                    # skip if same card as currently playing
                    if text == current_uri or text == last_played_uri:
                        print("Card is for current or last played URI; ignoring.")
                        continue
                    if text.startswith("spotify:") or text.startswith("playlist:") or text.startswith("album:") or text.startswith("track:"):
                        print(f"Playing Spotify URI from card: {text}")
                        sleep_time = time.time()
                        start_playback_uri(text)
                        time.sleep(1.0)
                        spotify_call(sp.shuffle, False, device_id=SPOTIFY_DEVICE_ID)
                        last_played_uri = text
                    else:
                        print(f"Tag text not recognized as Spotify URI: '{text}'")
                time.sleep(0.2)  # small delay between reads
            except Exception as inner_e:
                print(f"Error in NFC read loop iteration: {inner_e}")
                time.sleep(0.5)
    except Exception as e:
        print(f"Unexpected error in nfc_listener thread: {e}")

# -----------------------
# Attach handlers & start NFC thread
# -----------------------
first_encoder.when_rotated = update_volume
second_encoder.when_rotated_clockwise = update_forward_station
second_encoder.when_rotated_counter_clockwise = update_backward_station
switch.when_pressed = on_button_press

nfc_thread = threading.Thread(target=nfc_listener, daemon=True)
nfc_thread.start()

# -----------------------
# Main loop (keeps program alive)
# -----------------------
try:
    print("Main loop starting. Press Ctrl+C to exit.")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting on keyboard interrupt. Cleaning up GPIO and LEDs.")
    try:
        gpio_cleanup = getattr(GPIO, "cleanup", None)
        if gpio_cleanup:
            gpio_cleanup()
    except Exception as e:
        print(f"GPIO cleanup error: {e}")
    try:
        rgb_led.off()
    except Exception:
        pass
    print("Goodbye.")
