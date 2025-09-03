import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

# ---- CONFIG ----
SPOTIFY_DEVICE_ID = '450e2594318bbcc1e41ca3e88136e118c51a6dcb'
CLIENT_ID = 'c9f4f269f1804bf19f0fefee2539931a'
CLIENT_SECRET = 'e5a112f992ee43e9bbea57b8c19b053b'
REDIRECT_URI = 'http://10.0.0.217:8080/auth-response/'
SCOPE = 'user-modify-playback-state user-read-playback-state'
CACHE_PATH = "/home/diego/spotify_auth_cache2.json"

# ---- AUTH ----
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
    cache_path=CACHE_PATH
))

# ---- WRAPPER ----
def spotify_call(func, *args, **kwargs):
    """
    Runs a Spotify API call.
    If 'No active device' error occurs, force transfer playback to our device,
    wait briefly, then retry once.
    """
    try:
        return func(*args, **kwargs)
    except SpotifyException as e:
        if e.http_status == 404 and "NO_ACTIVE_DEVICE" in str(e):
            print("⚠️ No active device. Forcing playback to our device...")
            sp.transfer_playback(device_id=SPOTIFY_DEVICE_ID, force_play=True)
            time.sleep(0.5)  # give Spotify a moment to switch
            return func(*args, **kwargs)
        else:
            raise

# ---- CONTROLS ----
def set_volume(vol: int):
    """Set volume 0-100"""
    spotify_call(sp.volume, vol, device_id=SPOTIFY_DEVICE_ID)

def toggle_shuffle(state: bool):
    """Enable/disable shuffle"""
    spotify_call(sp.shuffle, state, device_id=SPOTIFY_DEVICE_ID)

def play_playlist(uri: str):
    """Start a playlist"""
    spotify_call(sp.start_playback, device_id=SPOTIFY_DEVICE_ID, context_uri=uri)

def next_track():
    """Skip forward"""
    spotify_call(sp.next_track, device_id=SPOTIFY_DEVICE_ID)

def prev_track():
    """Skip backward"""
    spotify_call(sp.previous_track, device_id=SPOTIFY_DEVICE_ID)

def pause():
    """Pause playback"""
    spotify_call(sp.pause_playback, device_id=SPOTIFY_DEVICE_ID)

def resume():
    """Resume playback"""
    spotify_call(sp.start_playback, device_id=SPOTIFY_DEVICE_ID)

# ---- DEMO ----
if __name__ == "__main__":
    play_playlist("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")  # Example playlist
    set_volume(50)
    toggle_shuffle(True)
    next_track()
