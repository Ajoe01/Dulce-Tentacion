from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import cloudinary 
import cloudinary.uploader 
import cloudinary.api 

# Cargar variables de entorno desde .env si existe
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Dios7es7bueno7_secret_key")

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# Detectar si estamos en Render (PostgreSQL) o local (SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # RENDER - PostgreSQL
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
    # LOCAL - SQLite
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
    try:
        if producto_nombre:
            import unicodedata
            producto_id = producto_nombre.lower()
            producto_id = ''.join(
                c for c in unicodedata.normalize('NFD', producto_id)
                if unicodedata.category(c) != 'Mn'
            )
            producto_id = ''.join(c if c.isalnum() else '_' for c in producto_id)
            producto_id = '_'.join(filter(None, producto_id.split('_')))
            public_id = f"dulce_tentacion/{producto_id}"
        else:
            import time
            public_id = f"dulce_tentacion/producto_{int(time.time())}"
        
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            overwrite=True,
            invalidate=True,
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto:good'}
            ]
        )
        return result['secure_url']
    except Exception as e:
        print(f"❌ Error subiendo a Cloudinary: {e}")
        return None

def delete_from_cloudinary(image_url):
    try:
        if image_url and "cloudinary.com" in image_url and image_url != PLACEHOLDER_URL:
            parts = image_url.split('/')
            upload_idx = -1
            for i, part in enumerate(parts):
                if part == 'upload':
                    upload_idx = i
                    break
            
            if upload_idx != -1 and upload_idx + 2 < len(parts):
                public_id_parts = parts[upload_idx + 2:]
                public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]
                cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"❌ Error eliminando de Cloudinary: {e}")

def init_db():
    conn = db()
    c = dict_cursor(conn)
    
    if DATABASE_URL:
        # PostgreSQL
        c.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                categoria_id INTEGER,
                nombre TEXT,
                descripcion TEXT,
                imagen TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS opciones (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER,
                nombre_opcion TEXT,
                precio INTEGER
            )
        """)
    else:
        # SQLite
        c.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria_id INTEGER,
                nombre TEXT,
                descripcion TEXT,
                imagen TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS opciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                nombre_opcion TEXT,
                precio INTEGER
            )
        """)
    
    # Solo cargar productos si la BD está vacía
    c.execute("SELECT COUNT(*) FROM productos")
    result = c.fetchone()
    
    # Manejar diferencias entre SQLite (tuple) y PostgreSQL (dict)
    if DATABASE_URL:
        productos_count = result['count'] if result else 0
    else:
        productos_count = result[0] if result else 0
    
    if productos_count == 0:
        print("📦 Base de datos vacía, cargando productos iniciales...")
        
        # Insertar categoría General
        if DATABASE_URL:
            c.execute("INSERT INTO categorias (nombre) VALUES (%s)", ("General",))
        else:
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", ("General",))
        
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
                    uploaded_url = upload_to_cloudinary(imagen, nombre)
                    if uploaded_url:
                        image_url = uploaded_url
                
                if DATABASE_URL:
                    c.execute(
                        "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s, %s, %s, %s) RETURNING id",
                        (categoria_id, nombre, descripcion, image_url)
                    )
                    prod_id = c.fetchone()['id']
                    
                    c.execute(
                        "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s, %s, %s)",
                        (prod_id, "Precio", int(precio))
                    )
                else:
                    c.execute(
                        "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?, ?, ?, ?)",
                        (categoria_id, nombre, descripcion, image_url)
                    )
                    prod_id = c.lastrowid
                    
                    c.execute(
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
                
                if imagen and imagen.filename and allowed_file(imagen.filename):
                    uploaded_url = upload_to_cloudinary(imagen, nombre)
                    
                    if uploaded_url:
                        if DATABASE_URL:
                            c.execute(
                                "UPDATE productos SET nombre = %s, descripcion = %s, imagen = %s WHERE id = %s",
                                (nombre, descripcion, uploaded_url, producto_id)
                            )
                        else:
                            c.execute(
                                "UPDATE productos SET nombre = ?, descripcion = ?, imagen = ? WHERE id = ?",
                                (nombre, descripcion, uploaded_url, producto_id)
                            )
                    else:
                        if DATABASE_URL:
                            c.execute(
                                "UPDATE productos SET nombre = %s, descripcion = %s WHERE id = %s",
                                (nombre, descripcion, producto_id)
                            )
                        else:
                            c.execute(
                                "UPDATE productos SET nombre = ?, descripcion = ? WHERE id = ?",
                                (nombre, descripcion, producto_id)
                            )
                else:
                    if DATABASE_URL:
                        c.execute(
                            "UPDATE productos SET nombre = %s, descripcion = %s WHERE id = %s",
                            (nombre, descripcion, producto_id)
                        )
                    else:
                        c.execute(
                            "UPDATE productos SET nombre = ?, descripcion = ? WHERE id = ?",
                            (nombre, descripcion, producto_id)
                        )
                
                if DATABASE_URL:
                    c.execute(
                        "UPDATE opciones SET precio = %s WHERE producto_id = %s",
                        (int(precio), producto_id)
                    )
                else:
                    c.execute(
                        "UPDATE opciones SET precio = ? WHERE producto_id = ?",
                        (int(precio), producto_id)
                    )
                
                conn.commit()
                print(f"✅ Producto actualizado: {nombre}")
            
            elif action == "delete":
                producto_id = request.form.get("producto_id")
                
                if DATABASE_URL:
                    c.execute("SELECT imagen FROM productos WHERE id = %s", (producto_id,))
                    img_row = c.fetchone()
                    if img_row:
                        img_url = img_row['imagen']
                        if img_url != PLACEHOLDER_URL:
                            delete_from_cloudinary(img_url)
                    
                    c.execute("DELETE FROM opciones WHERE producto_id = %s", (producto_id,))
                    c.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
                else:
                    c.execute("SELECT imagen FROM productos WHERE id = ?", (producto_id,))
                    img_row = c.fetchone()
                    if img_row:
                        img_url = img_row[0]
                        if img_url != PLACEHOLDER_URL:
                            delete_from_cloudinary(img_url)
                    
                    c.execute("DELETE FROM opciones WHERE producto_id = ?", (producto_id,))
                    c.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
                
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
    
    debug_mode = False
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
