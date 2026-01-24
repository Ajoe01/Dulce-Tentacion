import shutil
import os
from datetime import datetime

DB = "productos.db"
BACKUP_FOLDER = "backups"

def backup_database():
    """Hace un backup de la base de datos"""
    
    # Verificar que existe la base de datos
    if not os.path.exists(DB):
        print("❌ No se encontró productos.db")
        return False
    
    # Crear carpeta de backups si no existe
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
        print(f"📁 Carpeta '{BACKUP_FOLDER}' creada")
    
    # Generar nombre con fecha y hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"productos_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    
    # Copiar base de datos
    try:
        shutil.copy2(DB, backup_path)
        file_size = os.path.getsize(backup_path) / 1024  # KB
        print(f"\n✅ Backup creado exitosamente!")
        print(f"📄 Archivo: {backup_path}")
        print(f"📊 Tamaño: {file_size:.2f} KB")
        
        # Listar todos los backups
        backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.db')])
        print(f"\n📋 Total de backups: {len(backups)}")
        
        if len(backups) > 5:
            print(f"⚠️  Tienes {len(backups)} backups. Considera eliminar los antiguos.")
        
        return True
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return False

def list_backups():
    """Lista todos los backups disponibles"""
    if not os.path.exists(BACKUP_FOLDER):
        print("📁 No hay carpeta de backups")
        return
    
    backups = sorted([f for f in os.listdir(BACKUP_FOLDER) if f.endswith('.db')])
    
    if not backups:
        print("📋 No hay backups disponibles")
        return
    
    print(f"\n📋 Backups disponibles ({len(backups)}):\n")
    for idx, backup in enumerate(backups, 1):
        backup_path = os.path.join(BACKUP_FOLDER, backup)
        size = os.path.getsize(backup_path) / 1024
        mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
        print(f"  {idx}. {backup}")
        print(f"     Fecha: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Tamaño: {size:.2f} KB\n")

def restore_backup(backup_name):
    """Restaura un backup específico"""
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup no encontrado: {backup_name}")
        return False
    
    try:
        # Hacer backup del archivo actual antes de restaurar
        if os.path.exists(DB):
            temp_backup = f"productos_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DB, os.path.join(BACKUP_FOLDER, temp_backup))
            print(f"💾 Backup de seguridad creado: {temp_backup}")
        
        # Restaurar
        shutil.copy2(backup_path, DB)
        print(f"✅ Base de datos restaurada desde: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Error al restaurar: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    print("🔧 Utilidad de Backup para Dulce Tentación\n")
    
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "list":
            list_backups()
        elif comando == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("❌ Comando no válido")
            print("\nUso:")
            print("  python backup_db.py          - Crear backup")
            print("  python backup_db.py list     - Listar backups")
            print("  python backup_db.py restore <nombre>  - Restaurar backup")
    else:
        # Crear backup por defecto
        backup_database()
