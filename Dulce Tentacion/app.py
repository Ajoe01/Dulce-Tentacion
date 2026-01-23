from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Dios7es7bueno7_secret_key")

# Configuración de Cloudinary (desde variables de entorno)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

DB = "productos.db"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dios7es7bueno7")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
PLACEHOLDER_URL = "https://via.placeholder.com/300x300.png?text=Sin+Imagen"

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB máximo

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file):
    """Sube imagen a Cloudinary y retorna la URL"""
    try:
        result = cloudinary.uploader.upload(
            file,
            folder="dulce_tentacion",
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto:good'}
            ]
        )
        return result['secure_url']
    except Exception as e:
        print(f"Error subiendo a Cloudinary: {e}")
        return None

def delete_from_cloudinary(image_url):
    """Elimina imagen de Cloudinary"""
    try:
        if image_url and "cloudinary.com" in image_url:
            # Extraer public_id de la URL
            public_id = image_url.split('/')[-1].split('.')[0]
            public_id = f"dulce_tentacion/{public_id}"
            cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Error eliminando de Cloudinary: {e}")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    
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
            imagen TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS opciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            nombre_opcion TEXT,
            precio INTEGER,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    
    # Precarga con placeholder
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] == 0:
        categorias = {
            "Fresas con Crema": [
                ("Fresas con Crema - Pequeña", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Fresas con Crema - Mediana", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 PLACEHOLDER_URL, [("Precio", 15000)]),
                ("Fresas con Crema + Toppings", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 PLACEHOLDER_URL, [("Precio", 17000)]),
                ("Fresas con Crema + Helado", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 PLACEHOLDER_URL, [("Precio", 22000)]),
            ],
            "Menú Kids": [
                ("Copas Kids", "Copas para niños", PLACEHOLDER_URL, [("Precio", 8000)]),
                ("Canasta Kids", "Canasta con 2 porciones de helado + salsa + topping", PLACEHOLDER_URL, [("Precio", 9000)]),
            ],
            "Helados, Copas y Ensaladas": [
                ("Cono 1 bola", "Helado en cono de una bola", PLACEHOLDER_URL, [("Precio", 3500)]),
                ("Cono 2 bolas", "Helado en cono de dos bolas", PLACEHOLDER_URL, [("Precio", 6000)]),
                ("Canasta 2 bolas", "Canasta con dos bolas de helado", PLACEHOLDER_URL, [("Precio", 7000)]),
                ("Canasta 3 bolas", "Canasta con tres bolas de helado", PLACEHOLDER_URL, [("Precio", 9000)]),
                ("Canasta Frutal", "Canasta frutal especial", PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Ensalada de Frutas", "Fresca ensalada de frutas variadas", PLACEHOLDER_URL, [("Precio", 15000)]),
                ("Plato de Frutas con Helado", "Plato de frutas con helado y topping", PLACEHOLDER_URL, [("Precio", 12000)]),
                ("Copa Estándar", "3 porciones de helado + salsa + toppings", PLACEHOLDER_URL, [("Precio", 9000)]),
                ("Copa Premium", "Porción de fresas con crema, 2 porciones de helado frutas, piazza galletas, chocolate, salsa", PLACEHOLDER_URL, [("Precio", 24000)]),
            ],
            "Obleas": [
                ("Oblea Sencilla", "Oblea sencilla con dulce de leche", PLACEHOLDER_URL, [("Precio", 2000)]),
                ("Oblea con Fresas", "Oblea con fresas y crema", PLACEHOLDER_URL, [("Precio", 5000)]),
                ("Oblea Especial", "Oblea especial con toppings", PLACEHOLDER_URL, [("Precio", 8000)]),
            ],
        }
        
        for categoria_nombre, productos_list in categorias.items():
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", (categoria_nombre,))
            cat_id = c.lastrowid
            
            for nombre, descripcion, imagen, opciones in productos_list:
                c.execute("""
                    INSERT INTO productos (categoria_id, nombre, descripcion, imagen)
                    VALUES (?, ?, ?, ?)
                """, (cat_id, nombre, descripcion, imagen))
                prod_id = c.lastrowid
                
                for nombre_opcion, precio in opciones:
                    c.execute("""
                        INSERT INTO opciones (producto_id, nombre_opcion, precio)
                        VALUES (?, ?, ?)
                    """, (prod_id, nombre_opcion, precio))
        
        conn.commit()
    
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu():
    conn = db()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    opciones = conn.execute("SELECT * FROM opciones").fetchall()
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
        c = conn.cursor()
        
        try:
            if action == "add":
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                categoria_id = request.form.get("categoria_id", None)
                imagen = request.files.get("imagen")
                
                image_url = PLACEHOLDER_URL
                
                if imagen and imagen.filename and allowed_file(imagen.filename):
                    uploaded_url = upload_to_cloudinary(imagen)
                    if uploaded_url:
                        image_url = uploaded_url
                
                c.execute("""
                    INSERT INTO productos (categoria_id, nombre, descripcion, imagen)
                    VALUES (?, ?, ?, ?)
                """, (categoria_id, nombre, descripcion, image_url))
                prod_id = c.lastrowid
                
                c.execute(
                    "INSERT INTO opciones (producto_id, nombre_opcion, precio) VALUES (?, ?, ?)",
                    (prod_id, "Precio", int(precio))
                )
                conn.commit()
            
            elif action == "edit":
                producto_id = request.form.get("producto_id")
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                imagen = request.files.get("imagen")
                
                if imagen and imagen.filename and allowed_file(imagen.filename):
                    # Eliminar imagen anterior
                    old_img = c.execute("SELECT imagen FROM productos WHERE id = ?", (producto_id,)).fetchone()
                    if old_img and old_img[0] != PLACEHOLDER_URL:
                        delete_from_cloudinary(old_img[0])
                    
                    # Subir nueva imagen
                    uploaded_url = upload_to_cloudinary(imagen)
                    if uploaded_url:
                        c.execute("""
                            UPDATE productos SET nombre = ?, descripcion = ?, imagen = ?
                            WHERE id = ?
                        """, (nombre, descripcion, uploaded_url, producto_id))
                    else:
                        c.execute("""
                            UPDATE productos SET nombre = ?, descripcion = ?
                            WHERE id = ?
                        """, (nombre, descripcion, producto_id))
                else:
                    c.execute("""
                        UPDATE productos SET nombre = ?, descripcion = ?
                        WHERE id = ?
                    """, (nombre, descripcion, producto_id))
                
                c.execute("""
                    UPDATE opciones SET precio = ?
                    WHERE producto_id = ?
                """, (int(precio), producto_id))
                conn.commit()
            
            elif action == "delete":
                producto_id = request.form.get("producto_id")
                
                # Eliminar imagen de Cloudinary
                img_row = c.execute("SELECT imagen FROM productos WHERE id = ?", (producto_id,)).fetchone()
                if img_row and img_row[0] != PLACEHOLDER_URL:
                    delete_from_cloudinary(img_row[0])
                
                c.execute("DELETE FROM opciones WHERE producto_id = ?", (producto_id,))
                c.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
                conn.commit()
        
        except Exception as e:
            print(f"Error en editserver: {e}")
        finally:
            conn.close()
        
        return redirect("/editserver")
    
    # GET
    conn = db()
    productos = conn.execute("""
        SELECT p.*, o.precio 
        FROM productos p 
        LEFT JOIN opciones o ON p.id = o.producto_id
    """).fetchall()
    categorias = conn.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    
    return render_template("editserver.html", productos=productos, categorias=categorias)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
