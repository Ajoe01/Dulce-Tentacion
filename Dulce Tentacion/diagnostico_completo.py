import sqlite3
import os
from datetime import datetime

DB = "productos.db"

print("="*70)
print("🔍 DIAGNÓSTICO COMPLETO - DULCE TENTACIÓN")
print("="*70)

# 1. Verificar base de datos
print("\n📁 1. VERIFICANDO BASE DE DATOS:")
print("-" * 70)

if os.path.exists(DB):
    print(f"✅ {DB} EXISTE")
    stat = os.stat(DB)
    print(f"   📊 Tamaño: {stat.st_size / 1024:.2f} KB")
    print(f"   📅 Última modificación: {datetime.fromtimestamp(stat.st_mtime)}")
    print(f"   📍 Ubicación: {os.path.abspath(DB)}")
else:
    print(f"❌ {DB} NO EXISTE")
    print("   ⚠️ Este es el problema principal!")
    exit(1)

# 2. Verificar contenido
print("\n📊 2. CONTENIDO DE LA BASE DE DATOS:")
print("-" * 70)

try:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Contar productos
    c.execute("SELECT COUNT(*) FROM productos")
    total_productos = c.fetchone()[0]
    print(f"   📦 Total productos: {total_productos}")
    
    # Contar con imágenes
    c.execute("SELECT COUNT(*) FROM productos WHERE imagen IS NOT NULL AND imagen != ''")
    con_imagen = c.fetchone()[0]
    print(f"   🖼️  Con imagen: {con_imagen}")
    
    # Contar placeholders
    c.execute("SELECT COUNT(*) FROM productos WHERE imagen LIKE '%placeholder%'")
    placeholders = c.fetchone()[0]
    print(f"   🔲 Placeholders: {placeholders}")
    
    # Contar Cloudinary
    c.execute("SELECT COUNT(*) FROM productos WHERE imagen LIKE '%cloudinary%'")
    cloudinary = c.fetchone()[0]
    print(f"   ☁️  En Cloudinary: {cloudinary}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error accediendo a la base de datos: {e}")
    exit(1)

# 3. Mostrar todas las imágenes
print("\n🖼️  3. DETALLE DE IMÁGENES:")
print("-" * 70)

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("SELECT id, nombre, imagen FROM productos ORDER BY id")
productos = c.fetchall()

problemas = 0
for prod_id, nombre, imagen in productos:
    status = ""
    problema = False
    
    if not imagen or imagen == "":
        status = "❌ SIN IMAGEN"
        problema = True
    elif "placeholder" in imagen.lower():
        status = "🔲 PLACEHOLDER"
    elif imagen.startswith("http") and "cloudinary" in imagen:
        status = "✅ CLOUDINARY"
    elif imagen.startswith("http"):
        status = "🌐 URL EXTERNA"
    elif imagen.startswith("/"):
        status = "⚠️ RUTA LOCAL (PROBLEMA)"
        problema = True
    else:
        status = "❌ INVÁLIDA"
        problema = True
    
    if problema:
        problemas += 1
        print(f"\n   [{prod_id}] {nombre}")
        print(f"      Estado: {status}")
        print(f"      Imagen: {imagen[:80]}...")
    else:
        print(f"   [{prod_id}] {nombre}: {status}")

conn.close()

print(f"\n   📊 Productos con problemas: {problemas}/{total_productos}")

# 4. Verificar Cloudinary
print("\n☁️  4. CONFIGURACIÓN DE CLOUDINARY:")
print("-" * 70)

if os.path.exists('.env'):
    print("   ✅ Archivo .env existe")
    
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cloudinary_vars = {
        'CLOUDINARY_CLOUD_NAME': False,
        'CLOUDINARY_API_KEY': False,
        'CLOUDINARY_API_SECRET': False
    }
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key = line.split('=')[0].strip()
            value = line.split('=')[1].strip()
            if key in cloudinary_vars and value:
                cloudinary_vars[key] = True
    
    for key, configured in cloudinary_vars.items():
        status = "✅" if configured else "❌"
        print(f"   {status} {key}: {'Configurado' if configured else 'NO configurado'}")
    
    if all(cloudinary_vars.values()):
        print("\n   ✅ Cloudinary está completamente configurado")
    else:
        print("\n   ❌ Cloudinary NO está configurado correctamente")
else:
    print("   ❌ Archivo .env NO existe")

# 5. Resumen y recomendaciones
print("\n🎯 5. RESUMEN Y SOLUCIÓN:")
print("=" * 70)

if problemas > 0:
    print(f"\n⚠️  ENCONTRADOS {problemas} PRODUCTOS CON PROBLEMAS\n")
    
    print("📝 SOLUCIONES:")
    print("\n   Opción 1 - Corregir URLs (RECOMENDADO):")
    print("   → python fix_database.py")
    print("   → Esto pondrá placeholders en las imágenes problemáticas")
    
    print("\n   Opción 2 - Subir imágenes manualmente:")
    print("   → Ve a /editserver")
    print("   → Edita cada producto")
    print("   → Sube la imagen correcta")
    
    print("\n   Opción 3 - Ver imágenes huérfanas en Cloudinary:")
    print("   → python test_cloudinary.py")
    print("   → python clean_cloudinary.py")
else:
    print("\n✅ ¡TODO ESTÁ BIEN!")
    print("   Todas las imágenes tienen URLs válidas")

print("\n" + "=" * 70)
print("💡 Si el problema persiste, ejecuta:")
print("   python diagnostico_db.py monitor")
print("   (Para detectar cuándo y cómo cambian los datos)")
print("=" * 70 + "\n")
