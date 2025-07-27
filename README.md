# MediaSync-Daemon - Sistema de Reproducción Automática con VLC
Se ejecuta con `python MediaSync-Daemon.py`

## Descripción
MediaSync-Daemon es un sistema automatizado que gestiona la reproducción continua de videos mediante VLC, sincronizando contenido desde OneDrive y manteniendo la reproducción actualizada cuando se detectan cambios.
- Recomendación: Crear tarea en Task Manager para inicio ejecutar al inicio de sesion
- Opcional: Mantener un acceso directo en escritorio apuntando a `C:\Python312\python.exe C:\...\<dir>\MediaSync-Daemon\MediaSync-Daemon.py`

## Requisitos del Sistema

## Configuración de SharePoint y OneDrive

### Hacer disponible un directorio de SharePoint en OneDrive
1. Abrir el navegador web y acceder al sitio de SharePoint que contiene la biblioteca de videos
2. Navegar hasta la biblioteca de documentos deseada
3. Hacer clic en "Sincronizar" en la barra superior
4. Se abrirá OneDrive automáticamente y comenzará la sincronización

### Marcar como "Siempre disponible sin conexión"
1. Abrir OneDrive en el explorador de Windows
2. Localizar la carpeta sincronizada de SharePoint
3. Clic derecho en la carpeta
4. Seleccionar "Configurar siempre mantener en este dispositivo"
5. Esperar a que se complete la descarga inicial (círculo verde con palomita)

**Nota**: Es importante marcar como "Siempre disponible" el directorio entero para:
- Garantizar acceso inmediato a los videos
- Evitar problemas de streaming
- Permitir la detección confiable de cambios

## Configuracion del cliente
- Recomiendo configurar vlc para soportar una sola instancia
- Ajustar configuraciones en vlc para no mostrar titulos y transicionar suave entre videos
- Los videos se pueden cargar a un repo sharepoint, sin requisitos especificos aparte de extencion .mp4
- Se puede configurar la tarea programada manualmente, o mediante el script `$python create_task.py`

### Software
- Python 3.6 o superior
- VLC Media Player
- OneDrive configurado y sincronizado
- Windows OS (debido al uso de PowerShell para algunas funciones)

### Permisos
- Acceso de escritura al directorio temporal del sistema
- Acceso de lectura al directorio de OneDrive
- Permisos de administrador para configurar tareas programadas mediante `create_task.py`

## Configuración

### Estructura de Archivos
```
MediaSync-Daemon/
│
├── MediaSync-Daemon.py      # Script principal PUNTO DE ENTRADA
├── config.py           # Configuración centralizada
├── create_task.py      # Configurador de tarea programada
├── file_utils.py       # Utilidades de manejo de archivos
├── sync_utils.py       # Utilidades de sincronización
├── vlc_utils.py        # Utilidades de control de VLC
└── logging_utils.py    # Utilidades de logging
```

### Configuraciones Principales (config.py)

#### 1. Configuración del directorio OneDrive/SharePoint de Videos fuente
```python
VIDEO_CONFIG = {
    # Para carpeta personal de OneDrive:
    'VIDEO_DIR': r"C:\Users\<usuario>\OneDrive\...\videos",
    # Para biblioteca de SharePoint:
    # 'VIDEO_DIR': r"C:\Users\<usuario>\<Empresa>\<Sitio> - <Biblioteca>\videos",
    'VIDEO_EXTENSIONS': ['.mp4'],
    'MAX_FILE_SIZE_MB': 0  # 0 = sin límite
}
```

#### 2. Configuración de VLC
```python
VLC_CONFIG = {
    'VLC_EXE': r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    'VLC_ARGS': ['--loop', '--fullscreen']
}
```

#### 3. Configuración de Sincronización
```python
SYNC_CONFIG = {
    'DOWNLOAD_FINISH_DELAY': 2,    # segundos
    'REFRESH_CYCLE_DELAY': 10,     # segundos
    'MAX_CONSECUTIVE_ERRORS': 3
}
```

## Flujo de Funcionamiento

### 1. Inicialización
1. Validación de configuración
2. Configuración del sistema de logging
3. Verificación de archivos de video
4. Detención de instancias previas de VLC

### 2. Primera Ejecución
1. Validación de directorio de videos
2. Estimulación de sincronización OneDrive
3. Creación de directorio temporal
4. Copia de videos a directorio temporal
5. Generación de playlist
6. Inicio de VLC

### 3. Ciclo Principal
1. Monitoreo continuo del directorio de videos
2. Detección de cambios mediante sistema de cadena hash
3. En caso de cambios:
   - Detención de VLC
   - Actualización de archivos
   - Regeneración de playlist
   - Reinicio de VLC

### 4. Manejo de Errores
- Sistema de reintentos configurables
- Logging detallado de errores
- Límite de errores consecutivos

## Características de Seguridad
- Verificación de integridad de archivos
- Manejo de errores y loging
- Sistema de logging con rotación
- Validación de configuración al inicio

## Configuración de Inicio Automático

### Usando create_task.py
1. Ejecutar con permisos de administrador:
```bash
python create_task.py
```
2. Crea una tarea programada que:
   - Se ejecuta al inicio de sesión
   - Usa el intérprete de Python correcto
   - Mantiene los permisos necesarios

## Monitoreo y Mantenimiento

### Logs
- Ubicación: Mismo directorio que los videos OneDrive (Para monitorearlo remotamente desde el repo Sharepoint)
- Formato: `stream_status.log`
- Rotación: Configurada para mantener histórico manejable

### Archivo de Estado
- `stream_active.flag`: Indica el estado activo del script
- Archivos temporales en %TEMP%
  - Playlist
  - Copias de videos
  - Hash de estado

## Solución de Problemas
1. Verificar logs en `stream_status.log`
2. Comprobar existencia de `stream_active.flag`
3. Verificar permisos en directorios
4. Comprobar sincronización de OneDrive

## Limitaciones Conocidas
- Específico para Windows debido a uso de PowerShell
- Requiere OneDrive configurado
- Necesita VLC instalado en ruta predeterminada


---

*Para más detalles técnicos, consultar los comentarios en el código fuente*
