import os
import subprocess
import time
from logging_utils import log
from config import Config

class FileAccessError(Exception):
    pass

def verificar_archivo(file_path):
    """Verifica que un archivo esté completamente disponible"""
    try:
        # Obtener tamaño total del archivo
        size = os.path.getsize(file_path)
        
        if size == 0:
            log(f"WARNING: Archivo vacío detectado: {os.path.basename(file_path)}")
            return False
            
        # Leer el inicio del archivo
        with open(file_path, "rb") as f:
            f.seek(0)
            inicio = f.read(Config.SYNC_CONFIG['FILE_CHECK_BLOCK_SIZE'])
            
            # Leer el final del archivo si es lo suficientemente grande
            if size > Config.SYNC_CONFIG['MIN_FILE_SIZE_FOR_TAIL_CHECK']:
                f.seek(-Config.SYNC_CONFIG['FILE_CHECK_BLOCK_SIZE'], 2)
                final = f.read()
                
        return len(inicio) > 0
        
    except (IOError, OSError) as e:
        log(f"ERROR verificando archivo {os.path.basename(file_path)}: {e}")
        return False

def forzar_sync_powershell():
    """Estimula la sincronización de OneDrive usando PowerShell"""
    try:
        comando = r'Start-Process "$(Join-Path $env:LOCALAPPDATA \\Microsoft\\OneDrive\\OneDrive.exe)" "/sync"'
        subprocess.run(["powershell", "-Command", comando], 
                       capture_output=True,
                       text=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        log("Sincronización de OneDrive estimulada vía PowerShell")
    except Exception as e:
        log(f"ERROR al estimular sincronización de OneDrive: {e}")

def estimular_onedrive(files, video_dir):
    """'Toca' el directorio video_dir recursivamente para marcarlo como 'en uso' y forzar OneDrive Sync"""
    # Crear una lista de archivos que necesitan sincronización
    archivos_pendientes = []
    for f in files:
        file_path = os.path.join(video_dir, f)
        try:
            # Verificar atributos del archivo
            os.stat(file_path)
            
            # Verificar si el archivo está completo
            if not verificar_archivo(file_path):
                archivos_pendientes.append(f)
                continue
                
            # "Tocar" el archivo para forzar sincronización
            current_time = time.time()
            os.utime(file_path, (current_time, current_time))
            
        except Exception as e:
            log(f"ERROR accediendo a {f}: {e}")
            archivos_pendientes.append(f)
    
    # Reportar archivos pendientes y forzar sincronización si es necesario
    if archivos_pendientes:
        log(f"WARNING: {len(archivos_pendientes)} archivos requieren sincronización: {', '.join(archivos_pendientes)}")
        forzar_sync_powershell()
        return False
    
    # Si no hay archivos pendientes, aún así forzamos una sincronización periódica
    # pero con menos frecuencia (usando el timestamp del último archivo verificado)
    ultimo_archivo = max([os.path.getmtime(os.path.join(video_dir, f)) for f in files], default=0)
    if time.time() - ultimo_archivo > Config.SYNC_CONFIG['REFRESH_CYCLE_DELAY']:
        forzar_sync_powershell()
    
    return True
