# MediaSync-Daemon - Sistema de Reproducción Automática con VLC
Se ejecuta con `python MediaSync-Daemon.py`
Se ejecuta el script de creación de tarea automática con `python create_task.py`

## Descripción
MediaSync-Daemon es un sistema automatizado que gestiona la reproducción continua de videos mediante VLC, sincronizando contenido desde OneDrive y manteniendo la reproducción actualizada cuando se detectan cambios.
- Recomendación: Crear tarea en Task Manager para inicio ejecutar al inicio de sesion
- Opcional: Mantener un acceso directo en escritorio apuntando a `python C:\MediaSync-Daemon\MediaSync-Daemon.py`

## Requisitos del Sistema
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

## Configuracion del VLC
- Recomiendo configurar vlc para soportar una sola instancia
- Ajustar configuraciones en vlc para no mostrar titulos y transicionar suave entre videos
- Los videos se pueden cargar a un repo sharepoint, sin requisitos especificos aparte de extencion .mp4
- Se puede configurar la tarea programada manualmente, o mediante el script `$python create_task.py`

### Requisitos de Software
- Python 3.6 o superior
- VLC Media Player
- OneDrive configurado y sincronizado
- Windows OS (debido al uso de PowerShell para algunas funciones)

### Permisos
- Acceso de lectura y escritura al directorio temporal del sistema
- Acceso de lectura y escritura al directorio de OneDrive
- Permisos de administrador para configurar tareas programadas mediante `create_task.py`

## Configuración

### Estructura de Archivos
```
MediaSync-Daemon/
│
├── MediaSync-Daemon.py      # Script principal PUNTO DE ENTRADA
├── config.py                # Configuración centralizada
├── create_task.py           # Configurador de tarea programada
├── file_utils.py            # Utilidades de manejo de archivos
├── sync_utils.py            # Utilidades de sincronización OneDrive
├── vlc_utils.py             # Utilidades de control y validación de VLC
├── logging_utils.py         # Utilidades de logging con rotación
├── flujo-planeado.txt       # Algoritmo fuente y documentación de desarrollo
├── diagrama-flujo.png       # Diagrama visual del flujo del sistema
└── stream_active.flag       # Flag de estado (creado durante ejecución)
```

### Configuraciones Principales (config.py)

#### 1. Configuración del directorio OneDrive/SharePoint de Videos fuente
```python
VIDEO_CONFIG = {
    # Para carpeta personal de OneDrive:
    'VIDEO_DIR': r"C:\Users\<usuario>\OneDrive\...\videos",
    # Para biblioteca de SharePoint:
    # 'VIDEO_DIR': r"C:\Users\<usuario>\<Empresa>\<Sitio> - <Biblioteca>\videos",
    'FORMATOS_DE_VIDEO_ADMITIDOS': ['.mp4'],
    'MAX_FILE_SIZE_MB': 0  # 0 = sin límite
}
```

#### 2. Configuración de VLC
```python
VLC_CONFIG = {
    'VLC_EXE': r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    'VLC_ARGS': [
        '--loop',              # Reproducir en bucle
        '--fullscreen',        # Pantalla completa
        '--no-video-title-show', # No mostrar título al inicio
        '--no-video-title',    # No mostrar título en ventana
        '--video-on-top'       # Mantener video siempre visible
    ],
    'VLC_KILL_TIMEOUT': 3      # Timeout para cerrar VLC (segundos)
}
```

#### 3. Configuración de Sincronización
```python
SYNC_CONFIG = {
    'DOWNLOAD_FINISH_DELAY': 190,   # Espera post-estimulación OneDrive
    'REFRESH_CYCLE_DELAY': 1800,    # Intervalo de ciclo principal
    'VLC_PS_CHECK_TIME': 190,       # Intervalo de tiempo en el que se revisa que VLC se esté ejecutando, 
                                    # para relanzar si no lo está. 
    'MAX_SYNC_RETRIES': 3,          # Reintentos de sincronización
    'MAX_CONSECUTIVE_ERRORS': 3,    # Límite de errores consecutivos
    'ERROR_RETRY_DELAY': 5,         # Espera entre reintentos
    'MIN_FILE_SIZE_FOR_TAIL_CHECK': 16384,  # Tamaño mín. para verificación completa
    'FILE_CHECK_BLOCK_SIZE': 8192   # Tamaño de bloque para verificación
}
```

#### 4. Configuración de Logging
```python
LOG_CONFIG = {
    'LOG_PATH': os.path.join(VIDEO_CONFIG['VIDEO_DIR'], "MediaSync.log"),
    'LOG_LEVEL': 'INFO',
    'MAX_LOG_SIZE_MB': 10,
    'LOG_BACKUP_COUNT': 3,
    'LOG_ENCODING': 'utf-8'
}
```

## Flujo de Funcionamiento

### 1. Inicialización
1. Validación exhaustiva de configuración
2. Configuración del sistema de logging con rotación
3. Verificación de archivos de video disponibles
4. Detención de instancias previas de VLC
2. Configuración del sistema de logging
3. Verificación de archivos de video
4. Detención de instancias previas de VLC

### 2. Ciclo Principal de Monitoreo
1. **Validación continua de contenido**:
   - Verificación de archivos válidos en directorio fuente
   - Control de errores consecutivos con límite configurable
   - Sistema de reintentos automáticos

2. **Detección de cambios**:
   - Cálculo de hash del contenido del directorio
   - Comparación con hash anterior almacenado
   - Activación de actualización solo cuando hay cambios reales

3. **Actualización de contenido** (cuando se detectan cambios):
   - Detención segura de VLC con verificación de cierre
   - Limpieza de directorio temporal
   - Copia de nuevos archivos al directorio temporal
   - Regeneración de playlist con validación de archivos mp4
   - Actualización de hash de estado

4. **Gestión de VLC**:
   - Verificación de FLAG de estado antes de iniciar
   - Validación de playlist con contenido válido
   - Inicio de VLC con validaciones múltiples:
     - Verificación de ejecución exitosa usando psutil
     - Confirmación de proceso activo
     - Creación de FLAG solo si todo es exitoso

5. **Estimulación de OneDrive**:
   - "Toque" de archivos para forzar sincronización
   - Verificación de integridad de archivos
   - Comando PowerShell para estimular sincronización
   - Reportes detallados de estado de sincronización

### 3. Características Avanzadas

#### Verificación de Integridad de Archivos
- Lectura de bloques iniciales y finales
- Detección de transferencias incompletas
- Verificación de acceso y permisos

#### Sistema de FLAG de Estado
- `stream_active.flag`: Indica VLC ejecutándose
- Creación solo después de validaciones exitosas
- Eliminación automática al detener VLC
- Detección de procesos VLC huérfanos

#### Gestión Robusta de Procesos VLC
- Detección de procesos usando psutil
- Timeout configurable para cierre de procesos
- Limpieza automática de procesos fallidos
- Validación de ejecución antes de confirmar inicio

### 4. Manejo de Errores y Recuperación
- Sistema de reintentos configurables
- Logging detallado con niveles apropiados
- Límite de errores consecutivos
- Recuperación automática de estados inconsistentes
- Detección y limpieza de FLAG huérfanos

## Características de Seguridad y Robustez
- **Verificación de integridad de archivos** con lectura de bloques inicial/final
- **Validación exhaustiva de procesos VLC** usando psutil
- **Sistema de FLAG de estado** para prevenir ejecuciones múltiples
- **Manejo de errores con recuperación automática**
- **Sistema de logging con rotación automática**
- **Validación de configuración completa al inicio**
- **Detección y limpieza de procesos huérfanos**
- **Timeout configurable para operaciones críticas**

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

### Archivo de Estado y Temporales
- `stream_active.flag`: Indica estado activo de VLC (creado solo después de validaciones)
- Archivos temporales en `%TEMP%`:
  - `daemon_temp_media/`: Copia de videos para reproducción
  - `playlistVLC.m3u`: Playlist generada automáticamente
  - `daemon_media.hash`: Hash de estado para detección de cambios

### Estados del Sistema
- **FLAG existe + VLC activo**: Funcionamiento normal
- **FLAG existe + VLC inactivo**: Posible crash de VLC (se limpia automáticamente)
- **FLAG no existe + VLC activo**: Estado inconsistente (se corrige automáticamente)
- **FLAG no existe + VLC inactivo**: Estado de espera normal

## Solución de Problemas

### Problemas Comunes
1. **VLC no inicia**:
   - Verificar logs para detalles de validación
   - Comprobar playlist en `%TEMP%\playlistVLC.m3u`
   - Verificar permisos de ejecución de VLC
   
2. **Sincronización OneDrive lenta**:
   - Revisar estimulación en logs
   - Verificar "Siempre disponible sin conexión"
   - Comprobar velocidad de conexión

3. **FLAG huérfano persistente**:
   - El sistema detecta y limpia automáticamente
   - Verificar logs para procesos VLC huérfanos
   
4. **Errores de integridad de archivos**:
   - Verificar sincronización completa de OneDrive
   - Comprobar espacio disponible en disco
   - Revisar permisos de directorio temporal


## Limitaciones Conocidas
- Específico para Windows debido a uso de PowerShell
- Requiere OneDrive configurado
- Necesita VLC instalado en ruta predeterminada (o editar la ruta en config.py)


---

*Para más detalles técnicos, consultar los comentarios en el código fuente*
