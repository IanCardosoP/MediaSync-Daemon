import os
# Configuración central del sistema de reproducción y sincronización

class Config:
    
    VIDEO_CONFIG = {
        'VIDEO_DIR': r"C:\VideosPantallas",         # Directorio principal donde se almacenan los videos
        'FORMATOS_DE_VIDEO_ADMITIDOS': ['.mp4'],    # Extensiones de video permitidas
        'MAX_FILE_SIZE_MB': 0                       # Tamaño máximo de archivo en MB (0 = sin límite)
    }

    VLC_CONFIG = {
        'VLC_EXE': r"C:\Program Files\VideoLAN\VLC\vlc.exe",  # Ruta al ejecutable de VLC
        'VLC_ARGS': [
            '--loop',                 # Reproducción continua
            '--fullscreen',           # Pantalla completa
            '--no-video-title-show',  # Ocultar título del video
            '--no-video-title',       # Ocultar título de ventana
            '--video-on-top'          # Mantener VLC siempre visible
        ],
        'VLC_KILL_TIMEOUT': 3  # Tiempo máximo de espera para cerrar VLC (segundos)
    }

    SYNC_CONFIG = {
        'DOWNLOAD_FINISH_DELAY': 2,        # Espera tras estimular sincronización (segundos)
        'REFRESH_CYCLE_DELAY': 3600,       # Intervalo del ciclo principal (segundos)
        'VLC_PS_CHECK_TIME': 180,           # Intervalo para verificar proceso VLC activo (segundos)
        'MAX_CONSECUTIVE_ERRORS': 3,        # Errores consecutivos permitidos antes de detener 
        'ERROR_RETRY_DELAY': 10,            # Espera entre reintentos tras error (segundos)
        'MIN_FILE_SIZE_FOR_TAIL_CHECK': 16384,  # Tamaño mínimo de archivo para verificación (bytes)
        'FILE_CHECK_BLOCK_SIZE': 8192       # Tamaño del bloque de lectura para verificación (bytes)
    }

    PATHS = {
        'TEMP_VIDEO_DIR': os.path.join(os.getenv("TEMP"), "daemon_temp_media"),  # Directorio temporal de reproducción
        'PLAYLIST_PATH': os.path.join(os.getenv("TEMP"), "playlistVLC.m3u"),     # Archivo de playlist VLC
        'HASH_FILE': os.path.join(os.getenv("TEMP"), "daemon_media.hash"),       # Archivo de control de cambios
        'FLAG_FILE': os.path.join(os.path.dirname(__file__), "stream_active.flag"),  # Indicador de estado del script
    }

    LOG_CONFIG = {
        'LOG_PATH': os.path.join(VIDEO_CONFIG['VIDEO_DIR'], "MediaSync.log"),  # Ruta del archivo de log
        'LOG_LEVEL': 'INFO',                # Nivel de logging
        'LOG_FORMAT': "%(asctime)s [%(levelname)s] - %(message)s",  # Formato del log
        'DATE_FORMAT': "%a %d/%m/%Y %H:%M:%S",  # Formato de fecha en logs
        'MAX_LOG_SIZE_MB': 10,               # Tamaño máximo del log antes de rotar (MB)
        'LOG_BACKUP_COUNT': 3,               # Cantidad de archivos de respaldo
        'LOG_ENCODING': 'utf-8',             # Codificación del archivo de log
        'LOG_BACKUP_PREFIX': 'MediaSync.log.'  # Prefijo de backups del log
    }

    @classmethod
    def validate(cls):
        """Valida la configuración actual y retorna una lista de errores"""
        errors = []
        
        if not os.path.isdir(cls.VIDEO_CONFIG['VIDEO_DIR']):
            errors.append(f"Directorio de videos no existe: {cls.VIDEO_CONFIG['VIDEO_DIR']}")
        
        video_encontrado = False
        for root, dirs, files in os.walk(cls.VIDEO_CONFIG['VIDEO_DIR']):
            for filename in files:
                if any(filename.lower().endswith(ext.lower()) for ext in cls.VIDEO_CONFIG['FORMATOS_DE_VIDEO_ADMITIDOS']):
                    video_encontrado = True
                    break
            if video_encontrado:
                break
        
        if not video_encontrado:
            errors.append(f"No se encontraron archivos de video válidos en: {cls.VIDEO_CONFIG['VIDEO_DIR']}")

        if not os.path.isfile(cls.VLC_CONFIG['VLC_EXE']):
            errors.append(f"Ejecutable de VLC no encontrado: {cls.VLC_CONFIG['VLC_EXE']}")
        
        if cls.SYNC_CONFIG['DOWNLOAD_FINISH_DELAY'] < 0:
            errors.append("DOWNLOAD_FINISH_DELAY no puede ser negativo")
        if cls.SYNC_CONFIG['REFRESH_CYCLE_DELAY'] < 0:
            errors.append("REFRESH_CYCLE_DELAY no puede ser negativo")
        if cls.SYNC_CONFIG['MAX_CONSECUTIVE_ERRORS'] < 0:
            errors.append("MAX_CONSECUTIVE_ERRORS no puede ser negativo")
        if cls.SYNC_CONFIG['ERROR_RETRY_DELAY'] < 0:
            errors.append("ERROR_RETRY_DELAY no puede ser negativo")
        if cls.SYNC_CONFIG['MIN_FILE_SIZE_FOR_TAIL_CHECK'] < 0:
            errors.append("MIN_FILE_SIZE_FOR_TAIL_CHECK no puede ser negativo")
        if cls.SYNC_CONFIG['FILE_CHECK_BLOCK_SIZE'] <= 0:
            errors.append("FILE_CHECK_BLOCK_SIZE debe ser mayor que cero")
        if cls.VLC_CONFIG['VLC_KILL_TIMEOUT'] <= 0:
            errors.append("VLC_KILL_TIMEOUT debe ser mayor que cero")
        if cls.LOG_CONFIG['MAX_LOG_SIZE_MB'] <= 0:
            errors.append("MAX_LOG_SIZE_MB debe ser mayor que cero")
        if cls.LOG_CONFIG['LOG_BACKUP_COUNT'] < 0:
            errors.append("LOG_BACKUP_COUNT no puede ser negativo")
        if cls.LOG_CONFIG['LOG_ENCODING'] not in ['utf-8', 'latin-1', 'ascii']:
            errors.append(f"Codificación de log no válida: {cls.LOG_CONFIG['LOG_ENCODING']}")
        if cls.SYNC_CONFIG['VLC_PS_CHECK_TIME'] > cls.SYNC_CONFIG['REFRESH_CYCLE_DELAY'] * 0.5:
            errors.append("VLC_PS_CHECK_TIME debe permitir al menos dos chequeos por ciclo")
        
        if not cls.LOG_CONFIG['LOG_PATH'] or not os.path.isdir(os.path.dirname(cls.LOG_CONFIG['LOG_PATH'])):
            errors.append("La ruta del archivo de log no es válida o el directorio no existe")
        
        if not cls.VIDEO_CONFIG['VIDEO_DIR'] or not os.path.isdir(cls.VIDEO_CONFIG['VIDEO_DIR']):
            errors.append("La ruta del directorio de videos no es válida o no existe")

        return errors
