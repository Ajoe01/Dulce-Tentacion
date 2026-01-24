from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import cloudinary 
import cloudinary.uploader 
import cloudinary.api 

# Cargar variables de entorno desde .env si existe
if os.path.exists('.env'):
    print("📁 Cargando variables de entorno desde .env...")
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Dios7es7bueno7_secret_key")

# Configuración de Cloudinary (desde variables de entorno)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# Detectar si estamos en Render (PostgreSQL) o local (SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # RENDER - Usar PostgreSQL
    print("🐘 Usando PostgreSQL (Render)")
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from urllib.parse import urlparse
    
    url = urlparse(DATABASE_URL)
    
    def db():
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        return conn
    
    def dict_cursor(conn):
        return conn.cursor(cursor_factory=RealDictCursor)
else:
    # LOCAL - Usar SQLite
    print("💾 Usando SQLite (Local)")
    import sqlite3
    DB = "productos.db"
    
    def db():
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        return conn
    
    def dict_cursor(conn):
        return conn.cursor()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dios7es7bueno7")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
PLACEHOLDER_URL = "https://via.placeholder.com/300x300.png?text=Sin+Imagen"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB máximo

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file, producto_nombre=None):
    """Sube imagen a Cloudinary y retorna la URL
    
    Args:
        file: Archivo de imagen a subir
        producto_nombre: Nombre del producto para usar como public_id único
    """
    try:
        # Generar public_id único basado en el nombre del producto
        if producto_nombre:
            # Limpiar el nombre para usarlo como ID
            import unicodedata
            producto_id = producto_nombre.lower()
            # Remover acentos
            producto_id = ''.join(
                c for c in unicodedata.normalize('NFD', producto_id)
                if unicodedata.category(c) != 'Mn'
            )
            # Reemplazar espacios y caracteres especiales por guiones
            producto_id = ''.join(
                c if c.isalnum() else '_' for c in producto_id
            )
            # Remover guiones múltiples
            producto_id = '_'.join(filter(None, producto_id.split('_')))
            public_id = f"dulce_tentacion/{producto_id}"
        else:
            # Si no hay nombre, generar ID único con timestamp
            import time
            public_id = f"dulce_tentacion/producto_{int(time.time())}"
        
        print(f"📤 Subiendo imagen con ID: {public_id}")
        
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            overwrite=True,  # IMPORTANTE: Sobrescribir si ya existe
            invalidate=True,  # Invalidar cache de CDN
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto:good'}
            ]
        )
        
        print(f"✅ Imagen subida/actualizada: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return None

def delete_from_cloudinary(image_url):
    """Elimina imagen de Cloudinary usando la URL"""
    try:
        if image_url and "cloudinary.com" in image_url and image_url != PLACEHOLDER_URL:
            # Extraer public_id de la URL
            parts = image_url.split('/')
            # Buscar la parte después de 'upload/'
            upload_idx = -1
            for i, part in enumerate(parts):
                if part == 'upload':
                    upload_idx = i
                    break
            
            if upload_idx != -1 and upload_idx + 2 < len(parts):
                # El public_id incluye la carpeta y el nombre sin extensión
                public_id_parts = parts[upload_idx + 2:]
                public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]
                print(f"🗑️ Eliminando imagen: {public_id}")
                result = cloudinary.uploader.destroy(public_id)
                print(f"✅ Resultado: {result.get('result', 'unknown')}")
    except Exception as e:
        print(f"❌ Error eliminando de Cloudinary: {e}")

def init_db():
    conn = db()
    c = dict_cursor(conn)
    
    # Detectar tipo de base de datos para usar sintaxis correcta
    if DATABASE_URL:
        # PostgreSQL
        id_type = "SERIAL PRIMARY KEY"
        text_type = "TEXT"
    else:
        # SQLite
        id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        text_type = "TEXT"
    
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS categorias (
            id {id_type},
            nombre {text_type} UNIQUE
        )
    """)
    
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS productos (
            id {id_type},
            categoria_id INTEGER,
            nombre {text_type},
            descripcion {text_type},
            imagen {text_type},
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)
    
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS opciones (
            id {id_type},
            producto_id INTEGER,
            nombre_opcion {text_type},
            precio INTEGER,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    
    # SOLO precarga si NO hay productos (base de datos nueva)
    c.execute("SELECT COUNT(*) FROM productos")
    result = c.fetchone()
    productos_count = result[0] if isinstance(result, tuple) else result['count']
    
    if productos_count == 0:
        print("📦 Base de datos vacía, cargando productos iniciales...")
        categorias = {
            "Fresas con Crema": [
                ("Fresas con Crema - Pequeña", 
                 "Fresas, crema, mermelada de la casa, salsa de preferencia, topping de oreo.", 
                 PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Fresas con Crema - Mediana", 
                 "Fresas, crema, mermelada de la casa, salsa de preferencia, topping de oreo.", 
                 PLACEHOLDER_URL, [("Precio", 15000)]),
                ("Fresas con Crema + Toppings", 
                 "Fresas, crema, mermelada de la casa, salsa de preferencia, toppings.", 
                 PLACEHOLDER_URL, [("Precio", 17000)]),
                ("Fresas con Crema + Helado", 
                 "Fresas, crema, 1 porción de helado, queso, mermelada de la casa, salsa de preferencia, toppings.", 
                 PLACEHOLDER_URL, [("Precio", 22000)]),
            ],
            "Menú Kids": [
                ("Copas Kids", "2 porciones de helado, salsa, toppings.", PLACEHOLDER_URL, [("Precio", 8000)]),
                ("Canasta Kids", "2 porciones de helado, salsa, toppings.", PLACEHOLDER_URL, [("Precio", 9000)]),
            ],
            "Helados, Copas y Ensaladas": [
                ("Cono 1 bola", "Helado en cono de 1 porción, salsa, topping de oreo o chispitas de chocolate.", PLACEHOLDER_URL, [("Precio", 3500)]),
                ("Cono 2 bolas", "Helado en cono de 2 porciones, salsa, topping de oreo o chispitas de chocolate.", PLACEHOLDER_URL, [("Precio", 6000)]),
                ("Canasta 2 bolas", "Helado en canasta de 2 porciones, salsa, topping de oreo o piazza.", PLACEHOLDER_URL, [("Precio", 7000)]),
                ("Canasta 3 bolas", "Helado en canasta de 3 porciones, salsa, topping de oreo o piazza.", PLACEHOLDER_URL, [("Precio", 9000)]),
                ("Canasta Frutal", "Frutas, 1 porción de elado, salsa, crema de la casa, galleta.", PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Ensalada de Frutas", "Variedad de frutas, crema de la casa, 2 porciones de helado, salsa, queso, toppins.", PLACEHOLDER_URL, [("Precio", 15000)]),
                ("Plato de Frutas con Helado", "Plato de solo frutas con 2 porciones de helado.", PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Copa Estándar", "3 porciones de helado, salsa, toppings.", PLACEHOLDER_URL, [("Precio", 9000)]),
                ("Copa Premium", "Porción de fresas con crema, 2 porciones de helado,variedad de frutas, piazza, galletas, salsa de preferencia.", PLACEHOLDER_URL, [("Precio", 24000)]),
            ],
            "Obleas": [
                ("Oblea Sencilla", "Salsa, oreo triturada o chispitas de colores.", PLACEHOLDER_URL, [("Precio", 2000)]),
                ("Oblea con Fresas", "Fresas, crema de la casa, queso, salsas, oreo triturada.", PLACEHOLDER_URL, [("Precio", 5000)]),
                ("Oblea Especial", "Frutas, cremade la casa, queso, salsas, oreo triturada.", PLACEHOLDER_URL, [("Precio", 8000)]),
            ],
        }
        
        for categoria_nombre, productos_list in categorias.items():
            c.execute("INSERT INTO categorias (nombre) VALUES (%s)" if DATABASE_URL else "INSERT INTO categorias (nombre) VALUES (?)", 
                     (categoria_nombre,))
            
            if DATABASE_URL:
                c.execute("SELECT lastval()")
                cat_id = c.fetchone()[0]
            else:
                cat_id = c.lastrowid
            
            for nombre, descripcion, imagen, opciones in productos_list:
                c.execute(
                    "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s, %s, %s, %s)" if DATABASE_URL else 
                    "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?, ?, ?, ?)",
                    (cat_id, nombre, descripcion, imagen)
                )
                
                if DATABASE_URL:
                    c.execute("SELECT lastval()")
                    prod_id = c.fetchone()[0]
                else:
                    prod_id = c.lastrowid
                
                for nombre_opcion, precio in opciones:
                    c.execute(
                        "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s, %s, %s)" if DATABASE_URL else
                        "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?, ?, ?)",
                        (prod_id, nombre_opcion, precio)
                    )
        
        conn.commit()
        print("✅ Productos iniciales cargados")
    else:
        print(f"✅ Base de datos cargada con {productos_count} productos existentes")
    
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu():
    conn = db()
    c = dict_cursor(conn)
    categorias = c.execute("SELECT * FROM categorias").fetchall()
    productos = c.execute("SELECT * FROM productos").fetchall()
    opciones = c.execute("SELECT * FROM opciones").fetchall()
    conn.close()
    return render_template("menu.html", categorias=categorias, productos=productos, opciones=opciones)

@app.route("/carrito")
def carrito():
    return render_template("carrito.html")

@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/contacto")
def contacto():
    return render_template("contacto.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/editserver")
        else:
            return render_template("login.html", error="Contraseña incorrecta")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/")

@app.route("/editserver", methods=["GET", "POST"])
def editserver():
    if not session.get("admin_logged_in"):
        return redirect("/login")
    
    if request.method == "POST":
        action = request.form.get("action")
        conn = db()
        c = dict_cursor(conn)
        
        try:
            if action == "add":
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                categoria_id = request.form.get("categoria_id", None)
                imagen = request.files.get("imagen")
                
                image_url = PLACEHOLDER_URL
                
                if imagen and imagen.filename and allowed_file(imagen.filename):
                    print(f"📤 Subiendo imagen para: {nombre}")
                    uploaded_url = upload_to_cloudinary(imagen, nombre)
                    if uploaded_url:
                        image_url = uploaded_url
                        print(f"✅ Imagen guardada correctamente")
                    else:
                        print("❌ Error al subir imagen, usando placeholder")
                
                c.execute(
                    "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s, %s, %s, %s)" if DATABASE_URL else
                    "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?, ?, ?, ?)",
                    (categoria_id, nombre, descripcion, image_url)
                )
                
                if DATABASE_URL:
                    c.execute("SELECT lastval()")
                    prod_id = c.fetchone()[0]
                else:
                    prod_id = c.lastrowid
                
                c.execute(
                    "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s, %s, %s)" if DATABASE_URL else
                    "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?, ?, ?)",
                    (prod_id, "Precio", int(precio))
                )
                conn.commit()
                print(f"✅ Producto agregado: {nombre}")
            
            elif action == "edit":
                producto_id = request.form.get("producto_id")
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                imagen = request.files.get("imagen")
                
                print(f"📝 Editando producto ID: {producto_id} - {nombre}")
                
                # Si hay nueva imagen
                if imagen and imagen.filename and allowed_file(imagen.filename):
                    print(f"📤 Nueva imagen detectada para: {nombre}")
                    
                    # Subir nueva imagen (sobrescribirá la anterior si existe con el mismo nombre)
                    uploaded_url = upload_to_cloudinary(imagen, nombre)
                    
                    if uploaded_url:
                        print(f"✅ Nueva imagen subida/actualizada")
                        
                        # Actualizar con nueva imagen
                        c.execute(
                            "UPDATE productos SET nombre = %s, descripcion = %s, imagen = %s WHERE id = %s" if DATABASE_URL else
                            "UPDATE productos SET nombre = ?, descripcion = ?, imagen = ? WHERE id = ?",
                            (nombre, descripcion, uploaded_url, producto_id)
                        )
                    else:
                        print("❌ Error al subir nueva imagen, manteniendo datos sin cambiar imagen")
                        c.execute(
                            "UPDATE productos SET nombre = %s, descripcion = %s WHERE id = %s" if DATABASE_URL else
                            "UPDATE productos SET nombre = ?, descripcion = ? WHERE id = ?",
                            (nombre, descripcion, producto_id)
                        )
                else:
                    # No hay nueva imagen, solo actualizar texto
                    print("📝 Actualizando solo texto (sin cambiar imagen)")
                    c.execute(
                        "UPDATE productos SET nombre = %s, descripcion = %s WHERE id = %s" if DATABASE_URL else
                        "UPDATE productos SET nombre = ?, descripcion = ? WHERE id = ?",
                        (nombre, descripcion, producto_id)
                    )
                
                # Actualizar precio
                c.execute(
                    "UPDATE opciones SET precio = %s WHERE producto_id = %s" if DATABASE_URL else
                    "UPDATE opciones SET precio = ? WHERE producto_id = ?",
                    (int(precio), producto_id)
                )
                
                conn.commit()
                print(f"✅ Producto actualizado: {nombre}")
            
            elif action == "delete":
                producto_id = request.form.get("producto_id")
                
                print(f"🗑️ Eliminando producto ID: {producto_id}")
                
                # Eliminar imagen de Cloudinary
                c.execute(
                    "SELECT imagen FROM productos WHERE id = %s" if DATABASE_URL else
                    "SELECT imagen FROM productos WHERE id = ?",
                    (producto_id,)
                )
                img_row = c.fetchone()
                if img_row:
                    img_url = img_row[0] if isinstance(img_row, tuple) else img_row['imagen']
                    if img_url != PLACEHOLDER_URL:
                        print(f"🗑️ Eliminando imagen: {img_url}")
                        delete_from_cloudinary(img_url)
                
                c.execute(
                    "DELETE FROM opciones WHERE producto_id = %s" if DATABASE_URL else
                    "DELETE FROM opciones WHERE producto_id = ?",
                    (producto_id,)
                )
                c.execute(
                    "DELETE FROM productos WHERE id = %s" if DATABASE_URL else
                    "DELETE FROM productos WHERE id = ?",
                    (producto_id,)
                )
                conn.commit()
                print(f"✅ Producto eliminado")
        
        except Exception as e:
            print(f"❌ Error en editserver: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
        
        return redirect("/editserver")
    
    # GET
    conn = db()
    c = dict_cursor(conn)
    productos = c.execute("""
        SELECT p.*, o.precio 
        FROM productos p 
        LEFT JOIN opciones o ON p.id = o.producto_id
    """).fetchall()
    categorias = c.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    
    return render_template("editserver.html", productos=productos, categorias=categorias)

if __name__ == "__main__":
    print("🚀 Iniciando servidor...")
    print(f"🔐 Cloudinary configurado: {bool(os.environ.get('CLOUDINARY_CLOUD_NAME'))}")
    
    # IMPORTANTE: Usar debug=False en producción para evitar recargas
    debug_mode = False  # Cambiar a True solo para desarrollo
    
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
