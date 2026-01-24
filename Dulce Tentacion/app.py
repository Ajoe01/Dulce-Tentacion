from flask import Flask, render_template, request, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import cloudinary 
import cloudinary.uploader 
import cloudinary.api 

# 1. CARGAR VARIABLES DE ENTORNO
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Dios7es7bueno7_secret_key")

# 2. CONFIGURACIÓN CLOUDINARY
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# 3. CONFIGURACIÓN DE BASE DE DATOS
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from urllib.parse import urlparse
    url = urlparse(DATABASE_URL)
    def db():
        return psycopg2.connect(
            database=url.path[1:], user=url.username, password=url.password,
            host=url.hostname, port=url.port
        )
    def dict_cursor(conn):
        return conn.cursor(cursor_factory=RealDictCursor)
else:
    import sqlite3
    DB = "productos.db"
    def db():
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        return conn
    def dict_cursor(conn):
        return conn.cursor()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dios7es7bueno7")
PLACEHOLDER_URL = "https://via.placeholder.com/300x300.png?text=Sin+Imagen"

# 4. FUNCIONES DE APOYO
def upload_to_cloudinary(file, nombre):
    try:
        import time
        public_id = f"dulce_tentacion/prod_{int(time.time())}"
        result = cloudinary.uploader.upload(file, public_id=public_id)
        return result['secure_url']
    except: return PLACEHOLDER_URL

def delete_from_cloudinary(url):
    try:
        if "cloudinary" in url:
            p_id = url.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(f"dulce_tentacion/{p_id}")
    except: pass

# 5. INICIALIZACIÓN (AQUÍ ESTABA EL ERROR 500)
def init_db():
    conn = db(); c = dict_cursor(conn)
    id_t = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    c.execute(f"CREATE TABLE IF NOT EXISTS categorias (id {id_t}, nombre TEXT UNIQUE)")
    c.execute(f"CREATE TABLE IF NOT EXISTS productos (id {id_t}, categoria_id INTEGER, nombre TEXT, descripcion TEXT, imagen TEXT)")
    c.execute(f"CREATE TABLE IF NOT EXISTS opciones (id {id_t}, producto_id INTEGER, nombre_opcion TEXT, precio INTEGER)")
    
    c.execute("SELECT COUNT(*) FROM productos")
    res = c.fetchone()
    count = res[0] if isinstance(res, tuple) else list(res.values())[0]
    
    if count == 0:
        c.execute("INSERT INTO categorias (nombre) VALUES (%s)" if DATABASE_URL else "INSERT INTO categorias (nombre) VALUES (?)", ("General",))
        conn.commit()
    conn.close()

init_db()

# 6. RUTAS PÚBLICAS
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

@app.route("/carrito")
def carrito(): return render_template("carrito.html")

@app.route("/info")
def info(): return render_template("info.html")

@app.route("/contacto")
def contacto(): return render_template("contacto.html")

# 7. ADMINISTRACIÓN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/editserver")
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
        if action == "add":
            nom = request.form.get("nombre")
            desc = request.form.get("descripcion")
            pre = request.form.get("precio")
            cat = request.form.get("categoria_id")
            img = request.files.get("imagen")
            url = upload_to_cloudinary(img, nom) if img else PLACEHOLDER_URL
            
            c.execute("INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (%s,%s,%s,%s)" if DATABASE_URL else "INSERT INTO productos (categoria_id, nombre, descripcion, imagen) VALUES (?,?,?,?)", (cat, nom, desc, url))
            
            # Obtener ID insertado
            if DATABASE_URL:
                c.execute("SELECT lastval()"); rid = c.fetchone()
                pid = rid[0] if isinstance(rid, tuple) else rid['lastval']
            else: pid = c.lastrowid
            
            c.execute("INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (%s,%s,%s)" if DATABASE_URL else "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?,?,?)", (pid, "Precio", int(pre)))
            conn.commit()

        elif action == "delete":
            pid = request.form.get("producto_id")
            c.execute("DELETE FROM opciones WHERE producto_id = %s" if DATABASE_URL else "DELETE FROM opciones WHERE producto_id = ?", (pid,))
            c.execute("DELETE FROM productos WHERE id = %s" if DATABASE_URL else "DELETE FROM productos WHERE id = ?", (pid,))
            conn.commit()
        
        return redirect("/editserver")

    # Obtener datos para mostrar
    prods = c.execute("SELECT p.*, o.precio FROM productos p LEFT JOIN opciones o ON p.id = o.producto_id").fetchall()
    cats = c.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template("editserver.html", productos=prods, categorias=cats)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
