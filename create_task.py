import ctypes
import os
import subprocess
import sys
from pathlib import Path

def create_scheduled_task():
    """Crea una tarea programada para ejecutar playOnStart.py al inicio de sesión"""
    try:
        # Obtener rutas absolutas
        script_dir = Path(__file__).parent.absolute()
        script_path = script_dir / "playOnStart.py"
        
        # Verificar que el script existe
        if not script_path.exists():
            raise FileNotFoundError(f"No se encuentra el script: {script_path}")

        # Obtener la ruta absoluta de python.exe
        python_path = sys.executable

        # Crear el comando PowerShell que se ejecutará
        ps_command = f'''
        $action = New-ScheduledTaskAction -Execute "{python_path}" -Argument '"{script_path}"'
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
        Register-ScheduledTask -TaskName "playOnStart-VLC" `
                             -Action $action `
                             -Trigger $trigger `
                             -Settings $settings `
                             -Description "Ejecuta VLC al iniciar sesión" `
                             -User "$env:USERNAME" `
                             -Force
        Write-Output "Tarea programada creada con éxito."
        '''

        # Ejecutar PowerShell con privilegios elevados
        result = subprocess.run([
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-Command", ps_command
        ], capture_output=True, text=True)

        # Verificar resultado
        if result.returncode == 0:
            print("Tarea 'playOnStart-VLC' creada exitosamente.")
        else:
            print(f"ERROR al crear la tarea: {result.stderr}")

    except Exception as e:
        print(f"ERROR: No se pudo crear la tarea programada: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    # Verificar si se está ejecutando con privilegios de administrador
    if os.name == 'nt' and not ctypes.windll.shell32.IsUserAnAdmin():
        print("Este script requiere privilegios de administrador.")
        # Re-ejecutar el script con privilegios elevados
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1
        )
    else:
        create_scheduled_task()