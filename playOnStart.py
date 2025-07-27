import os
import shutil
import time
import sys
import logging.handlers
from config import Config
from logging_utils import configurar_logging, log
from vlc_utils import iniciar_vlc, detener_vlc
from file_utils import validar_videos, copiar_archivos, generar_playlist, limpiar_archivos_temporales
from sync_utils import forzar_sync_powershell, estimulate_onedrive_sync, FileAccessError

# Validar configuración antes de iniciar
config_errors = Config.validate()
if config_errors:
    print("Errores en la configuración:")
    for error in config_errors:
        print(f"- {error}")
    sys.exit(1)

# Excepción personalizada para errores de acceso a archivos
class FileAccessError(Exception):
    pass

# Variables globales para el control de errores
error_count = 0

# Acceso directo a configuraciones frecuentemente usadas
video_dir = Config.VIDEO_CONFIG['VIDEO_DIR']
vlc_exe = Config.VLC_CONFIG['VLC_EXE']
temp_video_dir = Config.PATHS['TEMP_VIDEO_DIR']
playlist_path = Config.PATHS['PLAYLIST_PATH']
hash_file = Config.PATHS['HASH_FILE']
flag_file = Config.PATHS['FLAG_FILE']
download_finish_delay = Config.SYNC_CONFIG['DOWNLOAD_FINISH_DELAY']
refresh_cycle_delay = Config.SYNC_CONFIG['REFRESH_CYCLE_DELAY']

# Inicializar el sistema de logging
configurar_logging()

log("---- INICIO DEL DAEMON STREAM ----")

######
# Bloque de Funciones
#######

# Calcula hash de los videos en video_dir
def calcular_hash(file_list):
    hashes = []
    missing_files = []
    
    for f in sorted(file_list):
        file_path = os.path.join(video_dir, f)
        try:
            size = os.path.getsize(file_path)
            hashes.append(f"{size}-{f}")
        except (FileNotFoundError, PermissionError) as e:
            missing_files.append(f)
            log(f"WARNING: No se puede acceder al archivo {f}: {e}")
    
    if missing_files:
        # Si hay archivos faltantes, lanzamos una excepción personalizada
        raise FileAccessError(f"No se puede acceder a {len(missing_files)} archivos: {', '.join(missing_files)}")
    
    return ";" if not hashes else ";".join(hashes)

######
# Bloque de primera ejecución 
#######

# 1. Validar acceso al ejecutable de VLC
if not os.path.exists(vlc_exe):
    log(f"ERROR: VLC no encontrado en {vlc_exe}")
    exit()

# 2. Validar que existen ficheros *.mp4 en video_dir
files = validar_videos(video_dir)
if not files:
    log(f"ERROR: No se encontraron archivos .mp4 en {video_dir}")
    exit()

# 3. Detener posibles instancias previas de VLC
detener_vlc()
time.sleep(1)  # Dar tiempo para que VLC se cierre completamente

# 4. Preparar directorios temporales
try:
    # Limpiar todo primero
    limpiar_archivos_temporales(incluir_activos=True)
    time.sleep(1)  # Esperar que se liberen recursos
    
    # Crear directorio temporal limpio
    os.makedirs(temp_video_dir, exist_ok=True)
except Exception as e:
    log(f"ERROR preparando directorios temporales: {str(e)}")
    exit()

# 5. Preparar reproducción inicial
try:
    log("Preparando reproducción inicial...")
    
    # Copiar archivos al directorio temporal
    log("Copiando archivos iniciales...")
    copiar_archivos(files, video_dir, temp_video_dir)
    
    # Generar playlist inicial
    log("Generando playlist inicial...")
    generar_playlist(files, temp_video_dir, playlist_path)
    
    # Iniciar reproducción
    log("Iniciando reproducción inicial...")
    iniciar_vlc()
    
    # Esperar un momento para asegurar que VLC inició correctamente
    time.sleep(2)
    
    # 6. Crear flag file si no existe
    if not os.path.exists(flag_file):
        open(flag_file, "w").close()
        log(f"Flag creado en {flag_file}")
        
    # 7. Forzar sincronización inicial de OneDrive
    log("Estimulando la sincronización inicial...")
    estimulate_onedrive_sync(files, video_dir)
    time.sleep(download_finish_delay)  # Esperar a que termine la sincronización
    
    # Guardar el hash inicial del contenido
    log("Guardando estado inicial...")
    old_hash = calcular_hash(files)
    with open(hash_file, "w", encoding="utf-8") as hf:
        hf.write(old_hash)
        
    log("Inicialización completada. Comenzando monitoreo...")
except Exception as e:
    log(f"ERROR durante la inicialización: {str(e)}")
    detener_vlc()
    limpiar_archivos_temporales(incluir_activos=True)
    exit()

log(f"INFO: Iniciando loop principal...")
######
# Bucle de ejecución
#######

# Bucle principal
error_count = 0
while True:
    
    try:
        
        time.sleep(refresh_cycle_delay)
        
        # Verificar archivos y manejar errores
        files = validar_videos(video_dir)
        if not files:
            log(f"WARNING: No se encontraron archivos .mp4 en {video_dir}")
            raise FileAccessError("No hay archivos de video disponibles")

        # Sincronización
        log("-> Estimulación de sincronización periódica en curso...")
        estimulate_onedrive_sync(files, video_dir)
        time.sleep(download_finish_delay)

        # Calcular y comparar hashes
        new_hash = calcular_hash(files)
        with open(hash_file, "r", encoding="utf-8") as hf:
            stored_hash = hf.read().strip()

        # Si llegamos aquí sin errores, resetear el contador
        error_count = 0

        # Verificar si hay cambios
        if new_hash != stored_hash:
            log("Cambios detectados... Preparando actualización")
            
            try:
                # 1. Detener VLC primero
                log("Deteniendo VLC para actualizar archivos...")
                detener_vlc()
                
                # 2. Esperar a que VLC se detenga completamente
                time.sleep(2)
                
                # 3. Limpiar directorio temporal
                if os.path.exists(temp_video_dir):
                    try:
                        shutil.rmtree(temp_video_dir, ignore_errors=True)
                        # Esperar un momento después de la eliminación
                        time.sleep(1)
                    except Exception as e:
                        log(f"Error al limpiar directorio temporal: {str(e)}")
                        raise
                
                # 4. Crear nuevo directorio temporal
                try:
                    os.makedirs(temp_video_dir)
                except Exception as e:
                    log(f"Error al crear directorio temporal: {str(e)}")
                    raise
                
                # 5. Copiar nuevos archivos
                try:
                    copiar_archivos(files, video_dir, temp_video_dir)
                except Exception as e:
                    log(f"Error al copiar archivos nuevos: {str(e)}")
                    raise
                        
                except Exception as e:
                    log(f"Error durante la actualización de archivos: {str(e)}")
                    raise
                
                # 6. Generar nueva playlist
                try:
                    # Si existe la playlist anterior, la eliminamos
                    if os.path.exists(playlist_path):
                        os.remove(playlist_path)
                    # Generar nueva playlist directamente en su ubicación final
                    generar_playlist(files, temp_video_dir, playlist_path)
                except Exception as e:
                    log(f"Error al actualizar playlist: {str(e)}")
                    raise
                
                # 7. Actualizar flag y hash
                try:
                    if os.path.exists(flag_file):
                        os.remove(flag_file)
                    open(flag_file, "w").close()
                    with open(hash_file, "w", encoding="utf-8") as hf:
                        hf.write(new_hash)
                except Exception as e:
                    log(f"Error al actualizar archivos de control: {str(e)}")
                    raise
                
                # 8. Iniciar VLC con el nuevo contenido
                iniciar_vlc()
                log("VLC reiniciado con contenido actualizado.")
                
            except Exception as e:
                log(f"ERROR durante la actualización: {str(e)}")
                
                # En caso de error, intentar recuperar el estado anterior
                try:
                    # Asegurar que VLC está detenido
                    detener_vlc()
                    time.sleep(2)  # Dar tiempo para que se liberen los recursos
                    
                    # Si el directorio temporal está vacío o no existe, intentar recuperarlo
                    if not os.path.exists(temp_video_dir) or not os.listdir(temp_video_dir):
                        if os.path.exists(temp_video_dir):
                            shutil.rmtree(temp_video_dir, ignore_errors=True)
                            time.sleep(1)  # Esperar después de eliminar
                        
                        # Recrear el directorio y copiar los archivos originales
                        os.makedirs(temp_video_dir)
                        copiar_archivos(files, video_dir, temp_video_dir)
                        generar_playlist(files, temp_video_dir, playlist_path)
                        log("Recuperación de archivos completada.")
                    
                    # Intentar reiniciar VLC con el contenido recuperado
                    if os.path.exists(temp_video_dir) and os.listdir(temp_video_dir):
                        iniciar_vlc()
                        log("VLC reiniciado con contenido recuperado.")
                    else:
                        log("ERROR: No se pudo recuperar el contenido para VLC")
                        
                except Exception as recovery_error:
                    log(f"ERROR durante la recuperación: {recovery_error}")
                    # No relanzamos esta excepción para permitir que el bucle principal continúe
                
                raise  # Re-lanzar la excepción original para el manejo de errores principal
                
                # Si todo está listo, intentar reiniciar VLC
                try:
                    if os.path.exists(temp_video_dir) and os.listdir(temp_video_dir):
                        iniciar_vlc()
                        log("VLC reiniciado con contenido recuperado después del error.")
                    else:
                        log("ERROR: No se puede iniciar VLC, directorio de videos vacío o inexistente")
                except Exception as vlc_error:
                    log(f"ERROR al reiniciar VLC: {vlc_error}")
                
                raise  # Re-lanzar la excepción para el manejo de errores principal
        else:
            log("Sin cambios detectados...")

    except (FileAccessError, Exception) as e:
        log(f"ERROR: {str(e)}")
        error_count += 1
        
        # Limpiar archivos temporales después de cada error
        limpiar_archivos_temporales(incluir_activos=False)
        
        if error_count >= Config.SYNC_CONFIG['MAX_CONSECUTIVE_ERRORS']:
            log(f"ERROR: Demasiados errores consecutivos ({error_count}). Deteniendo el script.")
            # Limpieza final antes de terminar
            limpiar_archivos_temporales(incluir_activos=True)
            break
            
        log(f"Reintentando en {Config.SYNC_CONFIG['ERROR_RETRY_DELAY']} segundos... (Intento {error_count} de {Config.SYNC_CONFIG['MAX_CONSECUTIVE_ERRORS']})")
        time.sleep(Config.SYNC_CONFIG['ERROR_RETRY_DELAY'])