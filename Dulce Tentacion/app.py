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

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# Detectar Base de Datos
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    print("🐘 Usando PostgreSQL (Render)")
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from urllib.parse import urlparse
    
    url = urlparse(DATABASE_URL)
    
    def db():
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    
    def dict_cursor(conn):
        return conn.cursor(cursor_factory=RealDictCursor)
else:
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

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file, producto_nombre=None):
    try:
        import unicodedata
        import time
        if producto_nombre:
            producto_id = ''.join(c for c in unicodedata.normalize('NFD', producto_nombre.lower()) if unicodedata.category(c) != 'Mn')
            producto_id = ''.join(c if c.isalnum() else '_' for c in producto_id)
            public_id = f"dulce_tentacion/{'_'.join(filter(None, producto_id.split('_')))}"
        else:
            public_id = f"dulce_tentacion/producto_{int(time.time())}"
        
        result = cloudinary.uploader.upload(
            file, public_id=public_id, overwrite=True, invalidate=True,
            transformation=[{'width': 800, 'height': 800, 'crop': 'limit'}, {'quality': 'auto:good'}]
        )
        return result['secure_url']
    except Exception as e:
        print(f"❌ Error Cloudinary: {e}")
        return None

def delete_from_cloudinary(image_url):
    try:
        if image_url and "cloudinary.com" in image_url and image_url != PLACEHOLDER_URL:
            parts = image_url.split('/')
            upload_idx = next((i for i, part in enumerate(parts) if part == 'upload'), -1)
            if upload_idx != -1 and upload_idx + 2 < len(parts):
                public_id = '/'.join(parts[upload_idx + 2:]).rsplit('.', 1)[0]
                cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"❌ Error eliminando imagen: {e}")

# --- INICIALIZACIÓN DE DB CORREGIDA ---
def init_db():
    conn = db()
    c = dict_cursor(conn)
    
    id_type = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    c.execute(f"CREATE TABLE IF NOT EXISTS categorias (id {id_type}, nombre TEXT UNIQUE)")
    c.execute(f"CREATE TABLE IF NOT EXISTS productos (id {id_type}, categoria_id INTEGER, nombre TEXT, descripcion TEXT, imagen TEXT, FOREIGN KEY (categoria_id) REFERENCES categorias(id))")
    c.execute(f"CREATE TABLE IF NOT EXISTS opciones (id {id_type}, producto_id INTEGER, nombre_opcion TEXT, precio INTEGER, FOREIGN KEY (producto_id) REFERENCES productos(id))")
    
    c.execute("SELECT COUNT(*) FROM productos")
    res_count = c.fetchone()
    # Manejo de conteo para tupla o dict
    count = res_count[0] if isinstance(res_count, tuple) else (res_count['count'] if 'count' in res_count else list(res_count.values())[0])
    
    if count == 0:
        print("📦 Cargando productos iniciales...")
        categorias_data = {
            "Fresas con Crema": [("Fresas con Crema - Mediana", "Fresas, crema, mermelada.", PLACEHOLDER_URL, [("Precio", 15000)])],
            "Obleas": [("Oblea Especial", "Frutas y queso.", PLACEHOLDER_URL, [("Precio", 8000)])]
        }
        
        for cat_nom, prods in categorias_data.items():
            c.execute("INSERT INTO categorias (nombre) VALUES (%s)" if DATABASE_URL else "INSERT INTO categorias (nombre) VALUES (?)", (cat_nom,))
            if DATABASE_URL:
                c.execute("SELECT lastval()")
                r = c.fetchone()
                cat_id = r[0] if isinstance(r, tuple) else r['lastval']
            else:
                cat_id = c.lastrowid
                
            for nom, desc, img, ops in prods:
                c.execute("INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s,%s,%s,%s)" if DATABASE_URL else "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?,?,?,?)", (cat_id, nom, desc, img))
                if DATABASE_URL:
                    c.execute("SELECT lastval()")
                    rp = c.fetchone()
                    prod_id = rp[0] if isinstance(rp, tuple) else rp['lastval']
                else:
                    prod_id = c.lastrowid
                
                for o_nom, o_pre in ops:
                    c.execute("INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s,%s,%s)" if DATABASE_URL else "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?,?,?)", (prod_id, o_nom, o_pre))
        
        conn.commit()
    conn.close()

init_db()

# --- RUTAS ---

@app.route("/")
def index(): return render_template("index.html")

@app.route("/menu")
def menu():
    conn = db(); c = dict_cursor(conn)
    cats = c.execute("SELECT * FROM categorias").fetchall()
    prods = c.execute("SELECT * FROM productos").fetchall()
    ops = c.execute("SELECT * FROM opciones").fetchall()
    conn.close()
    return render_template("menu.html", categorias=cats, productos=prods, opciones=ops)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/editserver")
        return render_template("login.html", error="Incorrecto")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect("/")

@app.route("/editserver", methods=["GET", "POST"])
def editserver():
    if not session.get("admin_logged_in"): return redirect("/login")
    
    conn = db(); c = dict_cursor(conn)
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "add":
                nom = request.form.get("nombre"); desc = request.form.get("descripcion")
                pre = request.form.get("precio"); cat = request.form.get("categoria_id")
                img = request.files.get("imagen")
                url_img = upload_to_cloudinary(img, nom) if img else PLACEHOLDER_URL
                
                c.execute("INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s,%s,%s,%s)" if DATABASE_URL else "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?,?,?,?)", (cat, nom, desc, url_img))
                if DATABASE_URL:
                    c.execute("SELECT lastval()"); r = c.fetchone()
                    pid = r[0] if isinstance(r, tuple) else r['lastval']
                else: pid = c.lastrowid
                c.execute("INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s,%s,%s)" if DATABASE_URL else "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?,?,?)", (pid, "Precio", int(pre)))
            
            elif action == "delete":
                pid = request.form.get("producto_id")
                c.execute("SELECT imagen FROM productos WHERE id = %s" if DATABASE_URL else "SELECT imagen FROM productos WHERE id = ?", (pid,))
                row = c.fetchone()
                if row:
                    img_v = row[0] if isinstance(row, tuple) else row['imagen']
                    delete_from_cloudinary(img_v)
                c.execute("DELETE FROM opciones WHERE producto_id = %s" if DATABASE_URL else "DELETE FROM opciones WHERE producto_id = ?", (pid,))
                c.execute("DELETE FROM productos WHERE id = %s" if DATABASE_URL else "DELETE FROM productos WHERE id = ?", (pid,))
            
            conn.commit()
        except Exception as e: print(f"Error: {e}")
        finally: conn.close(); return redirect("/editserver")

    prods = c.execute("SELECT p.*, o.precio FROM productos p LEFT JOIN opciones o ON p.id = o.producto_id").fetchall()
    cats = c.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template("editserver.html", productos=prods, categorias=cats)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
