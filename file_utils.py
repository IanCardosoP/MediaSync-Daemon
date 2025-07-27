import os
import shutil
import time
from logging_utils import log
from config import Config

def limpiar_archivos_temporales(incluir_activos=False):
    """
    Limpia archivos temporales del sistema.
    Args:
        incluir_activos (bool): Si True, también limpia los archivos en uso actual
    """
    def _eliminar_seguro(path):
        """Elimina un archivo o directorio de forma segura"""
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                # Intentar primero con shutil.rmtree
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except:
                    # Si falla, intentar con comando del sistema
                    if os.name == 'nt':  # Windows
                        os.system(f'rd /s /q "{path}"')
                    else:  # Unix/Linux
                        os.system(f'rm -rf "{path}"')
                # Esperar un momento después de la eliminación
                if os.path.exists(path):
                    time.sleep(1)
        except Exception as e:
            log(f"Error al eliminar {path}: {str(e)}")
            
    temp_paths = []
    
    if incluir_activos:
        temp_paths.extend([
            Config.PATHS['TEMP_VIDEO_DIR'],
            Config.PATHS['PLAYLIST_PATH'],
            Config.PATHS['HASH_FILE']
        ])
    
    for path in temp_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception as e:
            log(f"Advertencia: No se pudo limpiar {path}: {e}")

def validar_videos(video_dir):
    """Encuentra videos en el directorio especificado según las extensiones permitidas"""
    extensiones = Config.VIDEO_CONFIG['VIDEO_EXTENSIONS']
    archivos = []
    for f in os.listdir(video_dir):
        if any(f.lower().endswith(ext.lower()) for ext in extensiones):
            # Si hay límite de tamaño configurado, verificarlo
            if Config.VIDEO_CONFIG['MAX_FILE_SIZE_MB'] > 0:
                size_mb = os.path.getsize(os.path.join(video_dir, f)) / (1024 * 1024)
                if size_mb > Config.VIDEO_CONFIG['MAX_FILE_SIZE_MB']:
                    log(f"ADVERTENCIA: Archivo {f} excede el tamaño máximo permitido")
                    continue
            archivos.append(f)
    return archivos

def copiar_archivos(files, src_dir, dest_dir):
    """Copia archivos de un directorio a otro"""
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        src = os.path.join(src_dir, f)
        dst = os.path.join(dest_dir, f)
        try:
            shutil.copy2(src, dst)
            log(f"Archivo copiado: {f}")
        except Exception as e:
            log(f"ERROR al copiar {f}: {e}")

def generar_playlist(files, dest_dir, playlist_path):
    """Genera una playlist para VLC"""
    with open(playlist_path, "w", encoding=Config.LOG_CONFIG['LOG_ENCODING']) as pl:
        for f in files:
            if any(f.lower().endswith(ext.lower()) for ext in Config.VIDEO_CONFIG['VIDEO_EXTENSIONS']):
                pl.write(os.path.join(dest_dir, f) + "\n")
    log("Playlist generada.")
