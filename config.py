import os

# to-do: previsto, mover el config.py al mismo directorio de sharepoint para facilitar la configuración remota

class Config:
    # Configuraciones públicas que pueden ser modificadas por el usuario
    VIDEO_CONFIG = {
        # El directorio compartido mediante OneDrive/SharePoint que contenga *.mp4
        # Comillas necesarias si contiene espacios
        # Ejemplo: 'C:\\Users\\cardo\\OneDrive\\Escritorio\\videos'
        # Nota: Se recomienda usar rutas absolutas para evitar problemas de resolución
        'VIDEO_DIR': r"C:\Users\Ian Cardoso\OneDrive - Villagroup\Escritorio\VideosPantallas",
        # Extensiones de video permitidas
        # Se pueden agregar más extensiones según sea necesario
        # Ejemplo: ['.mp4', '.mkv', '.avi']
        'VIDEO_EXTENSIONS': ['.mp4'],
        # Tamaño máximo de archivo permitido en MB (0 = sin límite)
        'MAX_FILE_SIZE_MB': 0
    }

    VLC_CONFIG = {
        # Directorio de instalación VLC. Comillas necesarias si contiene espacios
        'VLC_EXE': r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        # Argumentos adicionales para VLC
        # Se pueden agregar más argumentos según sea necesario
        # Ejemplo: ['--loop', '--fullscreen']
        # Nota: Se recomienda usar argumentos compatibles con la versión de VLC instalada
        'VLC_ARGS': [
            '--loop',              # Reproducir en bucle
            '--fullscreen',        # Pantalla completa
            '--no-video-title-show', # No mostrar título al inicio del video
            '--no-video-title',    # No mostrar título en la ventana
            '--video-on-top'       # Mantener video siempre visible
        ],
        # Tiempo máximo de espera para matar proceso VLC (segundos)
        # Si VLC no se cierra en este tiempo, se forzará su cierre
        # Nota: Este valor debe ser mayor que el tiempo de espera en _esperar_cierre_vlc (1 segundos por defecto)
        # Ejemplo: 3 segundos
        'VLC_KILL_TIMEOUT': 3
    }

    SYNC_CONFIG = {
        # Espera para terminar de descargar después de la estimulación de sincronización (segundos)
        # Este valor determina cuánto tiempo esperar después de estimular OneDrive
        # antes de considerar que la descarga ha finalizado
        'DOWNLOAD_FINISH_DELAY': 2,
        # Intervalo de ejecución del bucle principal (segundos) 30 minutos por defecto (1800 segundos)
        # Este valor determina cada cuánto tiempo se revisa el directorio de videos en bucle principal
        # y se actualiza la lista de reproducción suponiendo que no hay problemas de sincronización o de ficheros.
        'REFRESH_CYCLE_DELAY': 10,
        # Número máximo de errores consecutivos antes de detener el script (int)
        # Este valor determina cuántos errores consecutivos se toleran antes de considerar
        # que hay un problema grave y detener el script
        'MAX_CONSECUTIVE_ERRORS': 3,
        # Tiempo de espera entre reintentos cuando hay errores (segundos)
        # Este valor determina cuánto tiempo esperar antes de reintentar una operación fallida
        # como la estimulación de OneDrive o la verificación de archivos
        'ERROR_RETRY_DELAY': 2,
        # Tamaño mínimo para que un archivo sea verificado tanto al inicio como al final (bytes)
        # Este valor determina el tamaño mínimo de archivo para realizar una verificación
        # de integridad al inicio y al final del archivo, para detectar archivos incompletos
        'MIN_FILE_SIZE_FOR_TAIL_CHECK': 16384,
        # Tamaño del bloque de lectura para verificación de archivos (bytes)
        # Se usa para leer el inicio y final de los archivos durante la verificación
        # Este valor determina cuántos bytes se leen al inicio y al final del archivo
        # para verificar su integridad y disponibilidad
        'FILE_CHECK_BLOCK_SIZE': 8192
    }

    # Configuraciones de directorios temporales y archivos de sistema
    PATHS = {
        # Directorio temporal desde donde se hace la reproducción de medios
        # Se recomienda usar una ruta absoluta para evitar problemas de resolución
        'TEMP_VIDEO_DIR': os.path.join(os.getenv("TEMP"), "daemon_temp_media"),
        # Archivo de playlist
        'PLAYLIST_PATH': os.path.join(os.getenv("TEMP"), "playlistVLC.m3u"),
        # Archivo para detectar cambios en contenido
        'HASH_FILE': os.path.join(os.getenv("TEMP"), "daemon_media.hash"),
        # Indicador de estado del script
        'FLAG_FILE': os.path.join(os.path.dirname(__file__), "stream_active.flag"),
    }

    # Configuración de logging
    LOG_CONFIG = {
        # Ruta del archivo de log
        'LOG_PATH': os.path.join(VIDEO_CONFIG['VIDEO_DIR'], "MediaSync.log"),
        # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        'LOG_LEVEL': 'INFO',
        # Formato del mensaje de log
        'LOG_FORMAT': "%(asctime)s [%(levelname)s] - %(message)s",
        # Formato de la fecha en los logs
        'DATE_FORMAT': "%a %d/%m/%Y %H:%M:%S",
        # Tamaño máximo del archivo de log en MB antes de rotar
        'MAX_LOG_SIZE_MB': 10,
        # Número de archivos de backup a mantener
        'LOG_BACKUP_COUNT': 3,
        # Codificación del archivo de log
        'LOG_ENCODING': 'utf-8',
        # Prefijo para los archivos de backup
        'LOG_BACKUP_PREFIX': 'MediaSync.log.'
    }

    @classmethod
    def validate(cls):
        """Valida la configuración actual y retorna lista de errores si los hay"""
        errors = []
        
        # Validar directorio de videos
        if not os.path.isdir(cls.VIDEO_CONFIG['VIDEO_DIR']):
            errors.append(f"Directorio de videos no existe: {cls.VIDEO_CONFIG['VIDEO_DIR']}")
        
        # Validar que hay al menos un archivo de video válido
        video_encontrado = False
        for root, dirs, files in os.walk(cls.VIDEO_CONFIG['VIDEO_DIR']):
            for filename in files:
                # Solo verificar archivos que podrían ser videos (ignorar logs, etc.)
                if any(filename.lower().endswith(ext.lower()) for ext in cls.VIDEO_CONFIG['VIDEO_EXTENSIONS']):
                    video_encontrado = True
                    break
            if video_encontrado:
                break
        
        if not video_encontrado:
            errors.append(f"No se encontraron archivos de video válidos en: {cls.VIDEO_CONFIG['VIDEO_DIR']}")

        # Validar ejecutable VLC
        if not os.path.isfile(cls.VLC_CONFIG['VLC_EXE']):
            errors.append(f"Ejecutable de VLC no encontrado: {cls.VLC_CONFIG['VLC_EXE']}")
        
        # ...resto del código de validaciones numéricas...
        if cls.SYNC_CONFIG['DOWNLOAD_FINISH_DELAY'] < 0:
            errors.append("El tiempo de espera para descarga no puede ser negativo")
        if cls.SYNC_CONFIG['REFRESH_CYCLE_DELAY'] < 0:
            errors.append("El tiempo de ciclo de refresco no puede ser negativo")
        if cls.SYNC_CONFIG['MAX_CONSECUTIVE_ERRORS'] < 0:
            errors.append("El número máximo de errores consecutivos no puede ser negativo")
        if cls.SYNC_CONFIG['ERROR_RETRY_DELAY'] < 0:
            errors.append("El tiempo de espera entre reintentos no puede ser negativo")
        if cls.SYNC_CONFIG['MIN_FILE_SIZE_FOR_TAIL_CHECK'] < 0:
            errors.append("El tamaño mínimo de archivo para verificación no puede ser negativo")
        if cls.SYNC_CONFIG['FILE_CHECK_BLOCK_SIZE'] <= 0:
            errors.append("El tamaño del bloque de lectura para verificación debe ser mayor que cero")
        if cls.VLC_CONFIG['VLC_KILL_TIMEOUT'] <= 0:
            errors.append("El tiempo de espera para matar VLC debe ser mayor que cero")
        if cls.LOG_CONFIG['MAX_LOG_SIZE_MB'] <= 0:
            errors.append("El tamaño máximo del archivo de log debe ser mayor que cero")
        if cls.LOG_CONFIG['LOG_BACKUP_COUNT'] < 0:
            errors.append("El número de archivos de backup del log no puede ser negativo")
        if cls.LOG_CONFIG['LOG_ENCODING'] not in ['utf-8', 'latin-1', 'ascii']:
            errors.append(f"Código de codificación del log no válido: {cls.LOG_CONFIG['LOG_ENCODING']}")
        
        # Validar ruta de log válida
        if not cls.LOG_CONFIG['LOG_PATH'] or not os.path.isdir(os.path.dirname(cls.LOG_CONFIG['LOG_PATH'])):
            errors.append("La ruta del archivo de log no es válida o el directorio no existe")
        
        # Validar ruta de video válida  
        if not cls.VIDEO_CONFIG['VIDEO_DIR'] or not os.path.isdir(cls.VIDEO_CONFIG['VIDEO_DIR']):
            errors.append("La ruta del directorio de videos no es válida o no existe")

        return errors