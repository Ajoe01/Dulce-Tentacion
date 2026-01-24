import os
import sqlite3
import cloudinary
import cloudinary.api
import cloudinary.uploader

# Cargar variables de entorno desde .env si existe
if os.path.exists('.env'):
    print("📁 Cargando variables de entorno desde .env...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

DB = "productos.db"

def get_db_images():
    """Obtiene todas las URLs de imágenes de la base de datos"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT imagen FROM productos WHERE imagen IS NOT NULL")
    images = [row[0] for row in c.fetchall()]
    conn.close()
    return images

def get_cloudinary_images():
    """Obtiene todas las imágenes de Cloudinary en la carpeta dulce_tentacion"""
    try:
        all_resources = []
        next_cursor = None
        
        while True:
            result = cloudinary.api.resources(
                type="upload",
                prefix="dulce_tentacion/",
                max_results=500,
                next_cursor=next_cursor
            )
            
            all_resources.extend(result.get('resources', []))
            next_cursor = result.get('next_cursor')
            
            if not next_cursor:
                break
        
        return all_resources
    except Exception as e:
        print(f"❌ Error obteniendo imágenes de Cloudinary: {e}")
        return []

def clean_orphaned_images(dry_run=True):
    """
    Limpia imágenes en Cloudinary que no están en la base de datos
    
    Args:
        dry_run: Si es True, solo muestra qué se eliminaría sin hacerlo
    """
    print("\n🔍 Analizando imágenes...\n")
    
    # Obtener imágenes de la base de datos
    db_images = get_db_images()
    db_image_ids = set()
    
    for img_url in db_images:
        if img_url and "cloudinary.com" in img_url:
            # Extraer public_id de la URL
            parts = img_url.split('/')
            for i, part in enumerate(parts):
                if part == 'upload':
                    if i + 2 < len(parts):
                        public_id_parts = parts[i + 2:]
                        public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]
                        db_image_ids.add(public_id)
                    break
    
    print(f"📊 Imágenes en la base de datos: {len(db_image_ids)}")
    
    # Obtener imágenes de Cloudinary
    cloudinary_images = get_cloudinary_images()
    print(f"☁️  Imágenes en Cloudinary: {len(cloudinary_images)}")
    
    # Encontrar huérfanas
    orphaned = []
    for resource in cloudinary_images:
        public_id = resource['public_id']
        if public_id not in db_image_ids:
            orphaned.append(resource)
    
    print(f"\n🗑️  Imágenes huérfanas encontradas: {len(orphaned)}\n")
    
    if not orphaned:
        print("✅ No hay imágenes huérfanas. Todo está limpio!")
        return
    
    # Mostrar huérfanas
    total_size = 0
    for idx, resource in enumerate(orphaned, 1):
        size_mb = resource['bytes'] / 1024 / 1024
        total_size += resource['bytes']
        print(f"{idx}. {resource['public_id']}")
        print(f"   URL: {resource['secure_url']}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        print(f"   Creado: {resource.get('created_at', 'desconocido')}\n")
    
    print(f"💾 Espacio total a liberar: {total_size / 1024 / 1024:.2f} MB\n")
    
    if dry_run:
        print("⚠️  MODO DRY-RUN: No se eliminará nada.")
        print("   Para eliminar realmente, ejecuta: python clean_cloudinary.py --delete")
    else:
        print("⚠️  ¿Estás seguro de que quieres eliminar estas imágenes?")
        confirm = input("   Escribe 'SI' para confirmar: ")
        
        if confirm.upper() == 'SI':
            print("\n🗑️  Eliminando imágenes...\n")
            deleted_count = 0
            
            for resource in orphaned:
                try:
                    result = cloudinary.uploader.destroy(resource['public_id'])
                    if result.get('result') == 'ok':
                        print(f"✅ Eliminado: {resource['public_id']}")
                        deleted_count += 1
                    else:
                        print(f"⚠️  No se pudo eliminar: {resource['public_id']}")
                except Exception as e:
                    print(f"❌ Error eliminando {resource['public_id']}: {e}")
            
            print(f"\n✅ Eliminadas {deleted_count} de {len(orphaned)} imágenes")
            print(f"💾 Espacio liberado: {total_size / 1024 / 1024:.2f} MB")
        else:
            print("❌ Cancelado")

if __name__ == "__main__":
    import sys
    
    print("🧹 Limpieza de Cloudinary - Dulce Tentación\n")
    
    # Verificar configuración
    if not all([
        os.environ.get("CLOUDINARY_CLOUD_NAME"),
        os.environ.get("CLOUDINARY_API_KEY"),
        os.environ.get("CLOUDINARY_API_SECRET")
    ]):
        print("❌ Error: Cloudinary no está configurado")
        print("   Verifica tu archivo .env")
        exit(1)
    
    # Verificar base de datos
    if not os.path.exists(DB):
        print(f"❌ Error: No se encontró {DB}")
        exit(1)
    
    # Ejecutar
    dry_run = "--delete" not in sys.argv
    clean_orphaned_images(dry_run=dry_run)
