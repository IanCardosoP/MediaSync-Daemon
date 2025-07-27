import subprocess
from logging_utils import log
from config import Config

def iniciar_vlc():
    """Inicia VLC en loop y fullscreen"""
    vlc_exe = Config.VLC_CONFIG['VLC_EXE']
    vlc_args = Config.VLC_CONFIG['VLC_ARGS']
    playlist_path = Config.PATHS['PLAYLIST_PATH'] 

    args = [vlc_exe, playlist_path] + vlc_args
    try:
        subprocess.Popen(args)
        log("VLC iniciado.")
    except Exception as e:
        log(f"ERROR al iniciar VLC: {e}")

def detener_vlc():
    """Detiene VLC para recargar con la nueva playlist"""
    try:
        subprocess.call(["taskkill", "/IM", "vlc.exe", "/F"], stdout=subprocess.DEVNULL)
        log("VLC detenido para mantenimiento.")
    except Exception as e:
        log(f"ERROR al detener VLC: {e}")
