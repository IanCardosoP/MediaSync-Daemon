import os
import logging
import logging.handlers
import sys
from config import Config

def configurar_logging():
    """Configura el sistema de logging con rotación de archivos"""
    log_path = Config.LOG_CONFIG['LOG_PATH']
    log_dir = os.path.dirname(log_path)
    
    # Asegurar que el directorio de logs existe
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configurar el handler con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=Config.LOG_CONFIG['MAX_LOG_SIZE_MB'] * 1024 * 1024,
        backupCount=Config.LOG_CONFIG['LOG_BACKUP_COUNT'],
        encoding=Config.LOG_CONFIG['LOG_ENCODING']
    )
    
    # Configurar el formato
    formatter = logging.Formatter(
        fmt=Config.LOG_CONFIG['LOG_FORMAT'],
        datefmt=Config.LOG_CONFIG['DATE_FORMAT']
    )
    file_handler.setFormatter(formatter)
    
    # Configurar el logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_CONFIG['LOG_LEVEL']))
    
    # Remover handlers existentes si los hay
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Agregar el nuevo handler
    root_logger.addHandler(file_handler)
    
    # Agregar también un StreamHandler para la consola con el mismo formato
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("Sistema de logging iniciado con rotación de archivos")

def log(msg):
    """Función de logging centralizada"""
    logging.info(msg)
