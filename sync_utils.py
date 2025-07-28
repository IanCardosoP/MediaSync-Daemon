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
    """
    FUNCION CRITICA:
    Estimula la sincronización de OneDrive mediante 'toque' de archivos y comandos PowerShell.
    
    Esta función implementa una estrategia de dos niveles para forzar la sincronización:
    1. "Toca" archivos individuales actualizando sus timestamps (marca como modificados)
    2. Ejecuta comandos PowerShell para estimular OneDrive cuando es necesario
        Nota: no se ha detectado que dichos comandos requieran permisos de administrador
    
    Args:
        files (list): Lista de nombres de archivos específicos a procesar
        video_dir (str): Directorio base donde se encuentran los archivos
        
    Returns:
        bool: True si todos los archivos están sincronizados correctamente,
              False si hay archivos pendientes que requieren atención
              
    Proceso detallado:
        - Verifica la integridad de cada archivo individualmente
        - "Toca" archivos válidos para marcarlos como activos en OneDrive
        - Mantiene lista de archivos problemáticos para reporte
        - Fuerza sincronización inmediata si hay archivos pendientes
        - Implementa sincronización periódica basada en timestamps
    """
    # ========================================================================
    # FASE 1: INICIALIZACIÓN Y PREPARACIÓN
    # ========================================================================
    
    # Contenedor para archivos que necesitan atención especial
    # (archivos incompletos, inaccesibles o corruptos)
    archivos_pendientes = []
    
    # ========================================================================
    # FASE 2: PROCESAMIENTO INDIVIDUAL DE ARCHIVOS
    # ========================================================================
    
    for f in files:
        file_path = os.path.join(video_dir, f)
        
        try:
            # ----------------------------------------------------------------
            # PASO 2.1: Verificación básica de acceso al archivo
            # ----------------------------------------------------------------
            # os.stat() falla inmediatamente si:
            # - El archivo no existe
            # - No hay permisos de lectura
            # - El archivo está bloqueado por otro proceso
            os.stat(file_path)
            
            # ----------------------------------------------------------------
            # PASO 2.2: Verificación de integridad del archivo
            # ----------------------------------------------------------------
            # verificar_archivo() realiza verificaciones profundas:
            # - Tamaño del archivo > 0 bytes
            # - Lectura exitosa del bloque inicial (detecta corrupción temprana)
            # - Para archivos grandes: lectura del bloque final (detecta transferencias incompletas)
            if not verificar_archivo(file_path):
                # Archivo incompleto o corrupto - marcar para sincronización especial
                archivos_pendientes.append(f)
                continue  # Saltar al siguiente archivo sin procesamiento adicional
                
            # ----------------------------------------------------------------
            # PASO 2.3: "Tocar" archivo para estimular OneDrive
            # ----------------------------------------------------------------
            # Actualizar timestamp de acceso y modificación al momento actual
            # Esto hace que OneDrive detecte el archivo como "recientemente modificado"
            # y lo priorice en su cola de sincronización
            current_time = time.time()
            os.utime(file_path, (current_time, current_time))
            # Nota: os.utime(path, (access_time, modification_time))
            
        except Exception as e:
            # ----------------------------------------------------------------
            # MANEJO DE ERRORES DE ACCESO
            # ----------------------------------------------------------------
            # Posibles causas de excepción:
            # - FileNotFoundError: Archivo eliminado durante procesamiento
            # - PermissionError: Sin permisos de acceso/modificación
            # - OSError: Problemas de E/O del sistema de archivos
            log(f"ERROR accediendo a {f}: {e}")
            archivos_pendientes.append(f)
    
    # ========================================================================
    # FASE 3: DECISIÓN DE SINCRONIZACIÓN BASADA EN RESULTADOS
    # ========================================================================
    
    # ----------------------------------------------------------------
    # ESCENARIO A: HAY ARCHIVOS PROBLEMÁTICOS
    # ----------------------------------------------------------------
    if archivos_pendientes:
        # Estrategia: Sincronización inmediata y agresiva
        # OneDrive necesita ser "despertado" para procesar archivos problemáticos
        # que pueden estar en estado de sincronización parcial o fallida
        forzar_sync_powershell()
        return False  # Indica que hay problemas pendientes de resolución
    
    # ----------------------------------------------------------------
    # ESCENARIO B: TODOS LOS ARCHIVOS ESTÁN BIEN
    # ----------------------------------------------------------------
    # Implementar sincronización periódica preventiva
    # Basada en el archivo más recientemente modificado del conjunto
    
    # Encontrar el timestamp de modificación más reciente entre todos los archivos
    # max() con default=0 maneja el caso edge de lista vacía
    ultimo_archivo = max([os.path.getmtime(os.path.join(video_dir, f)) for f in files], default=0)
    
    # Calcular tiempo transcurrido desde la última modificación
    tiempo_transcurrido = time.time() - ultimo_archivo
    
    # Si ha pasado suficiente tiempo (configurado en REFRESH_CYCLE_DELAY de Config.py),
    # ejecutar sincronización preventiva para mantener OneDrive activo
    # Esto previene que OneDrive entre en modo "dormido" por inactividad prolongada
    if tiempo_transcurrido > Config.SYNC_CONFIG['REFRESH_CYCLE_DELAY']:
        # Sincronización periódica: menos agresiva que la de archivos problemáticos
        forzar_sync_powershell()
    
    return True  # Todos los archivos procesados exitosamente
