import subprocess
import psutil
import os
import time
from logging_utils import log
from config import Config

flag_file = Config.PATHS['FLAG_FILE']

# ============================================================================
# FUNCIONES HELPER PRIVADAS
# ============================================================================

def _obtener_procesos_vlc():
    """Obtiene lista de PIDs de procesos VLC activos"""
    procesos = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and 'vlc' in proc.info['name'].lower():
            procesos.append(proc.info['pid'])
    return procesos

# todo: acoplar a extensiones definidas en el config
def _verificar_archivo_existe_y_es_mp4(ruta_archivo):
    """Verifica que un archivo exista y sea mp4"""
    return (os.path.exists(ruta_archivo) and 
            ruta_archivo.lower().endswith('.mp4'))

# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def validar_playlist(playlist_path):
    """Valida que la playlist tenga al menos 1 archivo mp4 válido"""
    try:
        if not os.path.exists(playlist_path) or os.path.getsize(playlist_path) == 0:
            log("ERROR: Playlist no existe o está vacía")
            return False
            
        with open(playlist_path, "r", encoding=Config.LOG_CONFIG['LOG_ENCODING']) as pl:
            archivos_validos = sum(1 for linea in pl 
                                 if _verificar_archivo_existe_y_es_mp4(linea.strip()))
                        
        if archivos_validos >= 1:
            return True
        else:
            log("ERROR: Playlist no contiene archivos mp4 válidos")
            return False
            
    except Exception as e:
        log(f"ERROR validando playlist: {e}")
        return False

def validar_ejecucion_vlc(proceso_vlc):
    """Valida que VLC se haya ejecutado correctamente"""
    try:
        # Esperar a que VLC inicie completamente
        time.sleep(2)
        
        # Verificar si el proceso sigue corriendo
        if proceso_vlc.poll() is not None:
            log(f"ERROR: VLC terminó prematuramente (código: {proceso_vlc.poll()})")
            return False
            
        # Verificar con psutil que VLC esté realmente ejecutándose
        try:
            proceso_psutil = psutil.Process(proceso_vlc.pid)
            if not (proceso_psutil.is_running() and 'vlc' in proceso_psutil.name().lower()):
                log(f"ERROR: Proceso VLC no válido (PID: {proceso_vlc.pid})")
                return False
        except psutil.NoSuchProcess:
            log("ERROR: Proceso VLC no encontrado")
            return False
            
        return True
            
    except Exception as e:
        log(f"ERROR validando ejecución de VLC: {e}")
        return False

def iniciar_vlc():
    """Inicia VLC con validaciones y crea FLAG solo si todo es exitoso"""
    vlc_exe = Config.VLC_CONFIG['VLC_EXE']
    vlc_args = Config.VLC_CONFIG['VLC_ARGS']
    playlist_path = Config.PATHS['PLAYLIST_PATH']
    
    try:
        # 1. Validar playlist antes de iniciar VLC
        if not validar_playlist(playlist_path):
            log("ERROR: No se puede iniciar VLC - playlist inválida")
            return False
            
        # 2. Ejecutar VLC
        args = [vlc_exe, playlist_path] + vlc_args
        proceso_vlc = subprocess.Popen(args)
        
        # 3. Validar ejecución correcta
        if not validar_ejecucion_vlc(proceso_vlc):
            log("ERROR: VLC no se ejecutó correctamente")
            # Limpiar: terminar proceso fallido
            try:
                proceso_vlc.terminate()
            except:
                pass
            return False
        log("VLC iniciado exitosamente.")

            
        # 4. Crear FLAG solo si todo fue exitoso
        try:
            open(flag_file, "w").close()
            log(f"Flag creada. {flag_file}")
            return True
        except Exception as e:
            log(f"ERROR creando FLAG: {e}")
            # Limpiar: terminar VLC si no se puede crear FLAG
            try:
                proceso_vlc.terminate()
            except:
                pass
            return False
            
    except Exception as e:
        log(f"ERROR al iniciar VLC: {e}")
        return False

def detener_vlc():
    """Detiene VLC, confirma cierre y elimina FLAG"""
    try:
        # 1. Obtener procesos VLC activos
        procesos_vlc = _obtener_procesos_vlc()
        
        if not procesos_vlc:
            # No hay VLC corriendo, solo eliminar FLAG si existe
            _eliminar_flag()
            return True
            
        # 2. Terminar VLC usando taskkill
        log(f"Terminando {len(procesos_vlc)} proceso(s) VLC")
        subprocess.call(["taskkill", "/IM", "vlc.exe", "/F"], stdout=subprocess.DEVNULL)
        
        # 3. Confirmar cierre con timeout configurado
        vlc_cerrado = _esperar_cierre_vlc(procesos_vlc)
        
        if not vlc_cerrado:
            log("WARNING: VLC puede no haberse cerrado completamente")
        
        # 4. Eliminar FLAG independientemente del resultado
        _eliminar_flag()
        
        log("VLC detenido")
        return vlc_cerrado
        
    except Exception as e:
        log(f"ERROR al detener VLC: {e}")
        return False

def _esperar_cierre_vlc(procesos_vlc, timeout=None):
    """Espera a que los procesos VLC se cierren completamente"""
    # Usar configuración si no se especifica timeout
    if timeout is None:
        timeout = Config.VLC_CONFIG['VLC_KILL_TIMEOUT']
        
    for intento in range(timeout):
        time.sleep(1)
        procesos_restantes = []
        
        for pid in procesos_vlc:
            try:
                proceso = psutil.Process(pid)
                if proceso.is_running():
                    procesos_restantes.append(pid)
            except psutil.NoSuchProcess:
                # Proceso cerrado correctamente
                pass
        
        if not procesos_restantes:
            return True
            
    return False

def _eliminar_flag():
    """Elimina el FLAG file si existe"""
    try:
        if os.path.exists(flag_file):
            os.remove(flag_file)
    except Exception as e:
        log(f"ERROR eliminando FLAG: {e}")

def vlc_esta_activo():
    """Verifica si hay procesos VLC ejecutándose"""
    return len(_obtener_procesos_vlc()) > 0

