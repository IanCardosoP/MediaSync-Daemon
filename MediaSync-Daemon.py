import os
import time
import sys
from config import Config
from logging_utils import configurar_logging, log
from vlc_utils import iniciar_vlc, detener_vlc, vlc_esta_activo
from file_utils import validar_dir, copiar_archivos, generar_playlist, limpiar_archivos_temporales, calcular_hash, escribir_hash
from sync_utils import forzar_sync_powershell, estimular_onedrive, FileAccessError

# Inicializar el sistema de logging
configurar_logging()

# Validar configuración de config.py antes de iniciar
config_errors = Config.validate()
if config_errors:
    log("Errores en la configuración:")
    for error in config_errors:
        log(f"- {error}")
    sys.exit(1)

# Acceso directo a configuraciones frecuentemente usadas
video_dir = Config.VIDEO_CONFIG['VIDEO_DIR']
vlc_exe = Config.VLC_CONFIG['VLC_EXE']
temp_video_dir = Config.PATHS['TEMP_VIDEO_DIR']
playlist_path = Config.PATHS['PLAYLIST_PATH']
hash_file = Config.PATHS['HASH_FILE']
flag_file = Config.PATHS['FLAG_FILE']
download_delay = Config.SYNC_CONFIG['DOWNLOAD_FINISH_DELAY']
cycle_delay = Config.SYNC_CONFIG['REFRESH_CYCLE_DELAY']
max_consecutive_errors = Config.SYNC_CONFIG['MAX_CONSECUTIVE_ERRORS']
error_retry_delay = Config.SYNC_CONFIG['ERROR_RETRY_DELAY']

log("---- Inicio del MediaSync Daemon ----")

# Detener posibles instancias previas de VLC
detener_vlc()

while True:
    
    # MIENTRAS EN VIDEO_DIR NO HAY ALMENOS 1 FICHERO VALIDO
    error_count = 0
    media_content = validar_dir(video_dir)

    while not media_content:
        log(f"WARNING: SIN CONTENIDO VÁLIDO EN {video_dir}")

        try:
            estimular_onedrive(media_content or [], video_dir)
            time.sleep(download_delay)
            media_content = validar_dir(video_dir)

            if not media_content:
                error_count += 1
                log(f"Intento {error_count}/{max_consecutive_errors} sin contenido válido.")

        except FileAccessError as e:
            log(f"ERROR: Acceso a archivo denegado - {str(e)}")
            error_count += 1

        except Exception as e:
            log(f"ERROR: Excepción inesperada - {str(e)}")
            error_count += 1

        # Verificación del umbral de errores
        if error_count >= max_consecutive_errors:
            log(f"ERROR: Demasiados errores consecutivos ({error_count}). Deteniendo el script.")
            log("POSIBLE DESCONEXIÓN. SE DETIENE EL DAEMON.")
            sys.exit(1)

        log(f"Reintentando en {error_retry_delay} segundos... (Intento {error_count} de {max_consecutive_errors})")
        time.sleep(error_retry_delay)

    # CALCULAR HASH DE VIDEO_DIR
    new_hash = calcular_hash(media_content)

    #LEER HASH: DIFERENTE DE OLD_HASH O NO EXISTE OLD_HASH?
    old_hash = None
    if os.path.exists(hash_file):
        try:
            with open(hash_file, 'r', encoding=Config.LOG_CONFIG['LOG_ENCODING']) as f:
                old_hash = f.read().strip()
        except Exception as e:
            log(f"Sin cambios detectados contra hash anterior: {e}")

    # COMPARAR HASHES: EXISTE OLD_HASH Y DIFERENTE DE NEW_HASH?
    if new_hash != old_hash or old_hash is None:
        log(f"CAMBIOS DETECTADOS: {len(media_content)} archivos válidos encontrados en {video_dir}")
        
        # DETENER VLC PARA MANTENIMIENTO
        detener_vlc()
        
        # ACTUALIZAR CARPETA TEMPORAL INCLUIDO PATHS, PLAYLIST Y HASH_FILE
        limpiar_archivos_temporales(incluir_activos=True)
        copiar_archivos(media_content, video_dir, temp_video_dir)
        generar_playlist(media_content, temp_video_dir, playlist_path)
        escribir_hash(new_hash, hash_file)
        log("MONITOREO INICIALIZADO...")
    
    # NO EXISTE FLAG Y PLAYLIST TIENE CONTENIDO
    # todo: validar si los elementos en la playlist son “válidos” (por ejemplo, si son archivos multimedia reproducibles o accesibles) y actuar en consecuencia.
    if not os.path.exists(flag_file) and os.path.getsize(playlist_path) > 0:
        # INICIAR VLC CON NUEVO CONTENIDO Y CREAR FLAG
        iniciar_vlc()


        
    # Estado de OneDrive
    howisdoing = estimular_onedrive(media_content, video_dir)
    time.sleep(download_delay)
    if howisdoing:
        log("OneDrive está sincronizado exitosamente.")
    else:
        log("WARNING: OneDrive requiere atención - archivos pendientes detectados.")
    # Esperar el ciclo de refresco antes de la siguiente iteración
    time.sleep(cycle_delay)

    # Verificar si VLC sigue activo o fue cerrado inesperadamente para relanzarlo
    if os.path.exists(flag_file) and not vlc_esta_activo():
        log("WARNING: FLAG existe pero VLC no está activo - posible crash")
        iniciar_vlc()
        log("INFO: VLC reiniciado tras detectarse cerrado")