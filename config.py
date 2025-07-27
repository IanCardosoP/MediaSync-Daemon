import os

class Config:
    # Configuraciones públicas que pueden ser modificadas por el usuario
    VIDEO_CONFIG = {
        # El directorio compartido mediante OneDrive/SharePoint que contenga *.mp4
        'VIDEO_DIR': r"C:\Users\Ian Cardoso\OneDrive - Villagroup\Escritorio\VideosPantallas",
        # Extensiones de video permitidas
        'VIDEO_EXTENSIONS': ['.mp4'],
        # Tamaño máximo de archivo permitido en MB (0 = sin límite)
        'MAX_FILE_SIZE_MB': 0
    }

    VLC_CONFIG = {
        # Directorio de instalación VLC
        'VLC_EXE': r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        # Argumentos adicionales para VLC
        'VLC_ARGS': [
            '--loop',              # Reproducir en bucle
            '--fullscreen',        # Pantalla completa
            '--no-video-title-show', # No mostrar título al inicio del video
            '--no-video-title',    # No mostrar título en la ventana
            '--video-on-top'       # Mantener video siempre visible
        ],
        # Tiempo máximo de espera para matar proceso VLC (segundos)
        'VLC_KILL_TIMEOUT': 10
    }

    SYNC_CONFIG = {
        # Espera para terminar de descargar después de la estimulación de sincronización (segundos)
        'DOWNLOAD_FINISH_DELAY': 2,
        # Intervalo de ejecución del bucle principal (segundos) 30 minutos por defecto (1800 segundos)
        'REFRESH_CYCLE_DELAY': 10,
        # Número máximo de reintentos para operaciones de sincronización (int)
        'MAX_SYNC_RETRIES': 3,
        # Número máximo de errores consecutivos antes de detener el script (int)
        'MAX_CONSECUTIVE_ERRORS': 3,
        # Tiempo de espera entre reintentos cuando hay errores (segundos)
        'ERROR_RETRY_DELAY': 5,
        # Tamaño mínimo para que un archivo sea verificado tanto al inicio como al final (bytes)
        'MIN_FILE_SIZE_FOR_TAIL_CHECK': 16384,
        # Tamaño del bloque de lectura para verificación de archivos (bytes)
        # Se usa para leer el inicio y final de los archivos durante la verificación
        'FILE_CHECK_BLOCK_SIZE': 8192
    }

    # Configuraciones de directorios temporales y archivos de sistema
    PATHS = {
        # Directorio temporal para la reproducción de medios
        'TEMP_VIDEO_DIR': os.path.join(os.getenv("TEMP"), "playOnStart_temp_media"),
        # Archivo de playlist
        'PLAYLIST_PATH': os.path.join(os.getenv("TEMP"), "playlistVLC.m3u"),
        # Archivo para detectar cambios en contenido
        'HASH_FILE': os.path.join(os.getenv("TEMP"), "playOnStart_media.hash"),
        # Indicador de estado del script
        'FLAG_FILE': os.path.join(os.path.dirname(__file__), "stream_active.flag"),
    }

    # Configuración de logging
    LOG_CONFIG = {
        # Ruta del archivo de log
        'LOG_PATH': os.path.join(VIDEO_CONFIG['VIDEO_DIR'], "stream_status.log"),
        # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        'LOG_LEVEL': 'INFO',
        # Formato del mensaje de log
        'LOG_FORMAT': "%(asctime)s [%(levelname)s] - %(message)s",
        # Formato de la fecha en los logs
        'DATE_FORMAT': "%a %H:%M:%S",
        # Tamaño máximo del archivo de log en MB antes de rotar
        'MAX_LOG_SIZE_MB': 10,
        # Número de archivos de backup a mantener
        'LOG_BACKUP_COUNT': 3,
        # Codificación del archivo de log
        'LOG_ENCODING': 'utf-8',
        # Prefijo para los archivos de backup
        'LOG_BACKUP_PREFIX': 'stream_status.log.'
    }

    @classmethod
    def validate(cls):
        """Valida la configuración actual y retorna lista de errores si los hay"""
        errors = []
        
        # Validar directorio de videos
        if not os.path.isdir(cls.VIDEO_CONFIG['VIDEO_DIR']):
            errors.append(f"Directorio de videos no existe: {cls.VIDEO_CONFIG['VIDEO_DIR']}")
        
        # TODO
        # Validar contenido en VIDEO_DIR
        
        # Validar ejecutable VLC
        if not os.path.isfile(cls.VLC_CONFIG['VLC_EXE']):
            errors.append(f"Ejecutable de VLC no encontrado: {cls.VLC_CONFIG['VLC_EXE']}")
        
        # Validar tiempos
        if cls.SYNC_CONFIG['DOWNLOAD_FINISH_DELAY'] < 0:
            errors.append("El tiempo de espera para descarga no puede ser negativo")
        if cls.SYNC_CONFIG['REFRESH_CYCLE_DELAY'] < 0:
            errors.append("El tiempo de ciclo de refresco no puede ser negativo")
        
        return errors
