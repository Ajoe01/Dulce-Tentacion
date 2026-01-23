import sqlite3

DB = "productos.db"
PLACEHOLDER_URL = "https://via.placeholder.com/300x300.png?text=Sin+Imagen"

def fix_database():
    """Corrige las URLs de las imágenes en la base de datos"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Obtener todos los productos con imágenes
    c.execute("SELECT id, nombre, imagen FROM productos")
    productos = c.fetchall()
    
    fixed_count = 0
    for prod_id, nombre, imagen in productos:
        # Si la imagen no es una URL válida (no comienza con http), corregirla
        if imagen and not imagen.startswith('http'):
            print(f"🔧 Corrigiendo: {nombre} - imagen actual: {imagen}")
            c.execute("UPDATE productos SET imagen = ? WHERE id = ?", (PLACEHOLDER_URL, prod_id))
            fixed_count += 1
    
    conn.commit()
    
    print(f"\n✅ Base de datos corregida!")
    print(f"📊 {fixed_count} imágenes actualizadas al placeholder")
    print(f"📋 Total de productos: {len(productos)}")
    
    # Mostrar estado actual
    print("\n📋 Estado actual de productos:")
    c.execute("SELECT id, nombre, imagen FROM productos")
    for prod_id, nombre, imagen in c.fetchall():
        status = "✅" if imagen and imagen.startswith('http') else "❌"
        print(f"{status} [{prod_id}] {nombre}: {imagen[:50]}...")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando corrección de base de datos...")
    fix_database()