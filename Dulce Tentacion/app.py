from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = "Dios7es7bueno7_secret_key"

DB = "productos.db"
ADMIN_PASSWORD = "Dios7es7bueno7"
UPLOAD_FOLDER = "static/images/productos"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB máximo

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Crear imagen placeholder si no existe
def create_placeholder():
    placeholder_path = os.path.join(UPLOAD_FOLDER, "placeholder.png")
    if not os.path.exists(placeholder_path):
        img = Image.new('RGB', (300, 300), color='#ffb3ba')
        img.save(placeholder_path)

create_placeholder()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def optimize_image(filepath):
    """Optimiza imágenes para web"""
    try:
        img = Image.open(filepath)
        # Convertir a RGB si es necesario
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = background
        
        # Redimensionar si es muy grande
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Guardar optimizada
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error optimizando imagen: {e}")
        return False

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
    
    # Precarga con imagen placeholder
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] == 0:
        categorias = {
            "Fresas con Crema": [
                ("Fresas con Crema - Pequeña", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 "placeholder.png", [("Precio", 12000)]),
                ("Fresas con Crema - Mediana", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 "placeholder.png", [("Precio", 15000)]),
                ("Fresas con Crema + Toppings", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 "placeholder.png", [("Precio", 17000)]),
                ("Fresas con Crema + Helado", 
                 "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", 
                 "placeholder.png", [("Precio", 22000)]),
            ],
            "Menú Kids": [
                ("Copas Kids", "Copas para niños", "placeholder.png", [("Precio", 8000)]),
                ("Canasta Kids", "Canasta con 2 porciones de helado + salsa + topping", "placeholder.png", [("Precio", 9000)]),
            ],
            "Helados, Copas y Ensaladas": [
                ("Cono 1 bola", "Helado en cono de una bola", "placeholder.png", [("Precio", 3500)]),
                ("Cono 2 bolas", "Helado en cono de dos bolas", "placeholder.png", [("Precio", 6000)]),
                ("Canasta 2 bolas", "Canasta con dos bolas de helado", "placeholder.png", [("Precio", 7000)]),
                ("Canasta 3 bolas", "Canasta con tres bolas de helado", "placeholder.png", [("Precio", 9000)]),
                ("Canasta Frutal", "Canasta frutal especial", "placeholder.png", [("Precio", 12000)]),
                ("Ensalada de Frutas", "Fresca ensalada de frutas variadas", "placeholder.png", [("Precio", 15000)]),
                ("Plato de Frutas con Helado", "Plato de frutas con helado y topping", "placeholder.png", [("Precio", 12000)]),
                ("Copa Estándar", "3 porciones de helado + salsa + toppings", "placeholder.png", [("Precio", 9000)]),
                ("Copa Premium", "Porción de fresas con crema, 2 porciones de helado frutas, piazza galletas, chocolate, salsa", "placeholder.png", [("Precio", 24000)]),
            ],
            "Obleas": [
                ("Oblea Sencilla", "Oblea sencilla con dulce de leche", "placeholder.png", [("Precio", 2000)]),
                ("Oblea con Fresas", "Oblea con fresas y crema", "placeholder.png", [("Precio", 5000)]),
                ("Oblea Especial", "Oblea especial con toppings", "placeholder.png", [("Precio", 8000)]),
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
        error_msg = None
        
        try:
            if action == "add":
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                categoria_id = request.form.get("categoria_id", None)
                imagen = request.files.get("imagen")
                
                filename = "placeholder.png"
                
                if imagen and imagen.filename:
                    if allowed_file(imagen.filename):
                        filename = secure_filename(imagen.filename)
                        # Agregar timestamp para evitar conflictos
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        imagen.save(filepath)
                        
                        # Optimizar imagen
                        if not optimize_image(filepath):
                            os.remove(filepath)
                            filename = "placeholder.png"
                    else:
                        error_msg = "Formato de imagen no válido. Use: PNG, JPG, JPEG, GIF, WEBP"
                
                c.execute("""
                    INSERT INTO productos (categoria_id, nombre, descripcion, imagen)
                    VALUES (?, ?, ?, ?)
                """, (categoria_id, nombre, descripcion, filename))
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
                
                if imagen and imagen.filename:
                    if allowed_file(imagen.filename):
                        filename = secure_filename(imagen.filename)
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        imagen.save(filepath)
                        
                        if optimize_image(filepath):
                            # Eliminar imagen anterior si no es placeholder
                            old_img = c.execute("SELECT imagen FROM productos WHERE id = ?", (producto_id,)).fetchone()
                            if old_img and old_img[0] != "placeholder.png":
                                old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_img[0])
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                            
                            c.execute("""
                                UPDATE productos SET nombre = ?, descripcion = ?, imagen = ?
                                WHERE id = ?
                            """, (nombre, descripcion, filename, producto_id))
                        else:
                            os.remove(filepath)
                            c.execute("""
                                UPDATE productos SET nombre = ?, descripcion = ?
                                WHERE id = ?
                            """, (nombre, descripcion, producto_id))
                    else:
                        error_msg = "Formato de imagen no válido"
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
                
                # Eliminar imagen si no es placeholder
                img_row = c.execute("SELECT imagen FROM productos WHERE id = ?", (producto_id,)).fetchone()
                if img_row and img_row[0] != "placeholder.png":
                    img_path = os.path.join(app.config["UPLOAD_FOLDER"], img_row[0])
                    if os.path.exists(img_path):
                        os.remove(img_path)
                
                c.execute("DELETE FROM opciones WHERE producto_id = ?", (producto_id,))
                c.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
                conn.commit()
        
        except Exception as e:
            print(f"Error en editserver: {e}")
            error_msg = str(e)
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
