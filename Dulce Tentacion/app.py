from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "Dios7es7bueno7_secret_key"
DB = "productos.db"
ADMIN_PASSWORD = "Dios7es7bueno7"

UPLOAD_FOLDER = "static/images/productos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    # precarga solo si está vacío
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] == 0:
        # Insertar categorías
        categorias = {
            "Fresas con Crema": [
                ("Fresas con Crema - Pequeña", "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", "fresas.jpg", [("Precio", 12000)]),
                ("Fresas con Crema - Mediana", "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", "fresas.jpg", [("Precio", 15000)]),
                ("Fresas con Crema + Toppings", "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", "fresas.jpg", [("Precio", 17000)]),
                ("Fresas con Crema + Helado", "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", "fresas.jpg", [("Precio", 22000)]),
            ],
            "Menú Kids": [
                ("Copas Kids", "Copas para niños", "copas_kids.jpg", [("Precio", 8000)]),
                ("Canasta Kids", "Canasta con 2 porciones de helado + salsa + topping", "canasta_kids.jpg", [("Precio", 9000)]),
            ],
            "Helados, Copas y Ensaladas": [
                ("Cono 1 bola", "Helado en cono de una bola", "cono1.jpg", [("Precio", 3500)]),
                ("Cono 2 bolas", "Helado en cono de dos bolas", "cono2.jpg", [("Precio", 6000)]),
                ("Canasta 2 bolas", "Canasta con dos bolas de helado", "canasta2.jpg", [("Precio", 7000)]),
                ("Canasta 3 bolas", "Canasta con tres bolas de helado", "canasta3.jpg", [("Precio", 9000)]),
                ("Canasta Frutal", "Canasta frutal especial", "frutal.jpg", [("Precio", 12000)]),
                ("Ensalada de Frutas", "Fresca ensalada de frutas variadas", "ensalada_frutas.jpg", [("Precio", 15000)]),
                ("Plato de Frutas con Helado", "Plato de frutas con helado y topping", "plato_frutas_helado.jpg", [("Precio", 12000)]),
                ("Copa Estándar", "3 porciones de helado + salsa + toppings", "copa.jpg", [("Precio", 9000)]),
                ("Copa Premium", "Porción de fresas con crema, 2 porciones de helado frutas, piazza galletas, chocolate, salsa", "copa_premium.jpg", [("Precio", 24000)]),
            ],
            "Obleas": [
                ("Oblea Sencilla", "Oblea sencilla con dulce de leche", "oblea1.jpg", [("Precio", 2000)]),
                ("Oblea con Fresas", "Oblea con fresas y crema", "oblea2.jpg", [("Precio", 5000)]),
                ("Oblea Especial", "Oblea especial con toppings", "oblea3.jpg", [("Precio", 8000)]),
            ],
        }
        
        for categoria_nombre, productos_list in categorias.items():
            # Crear categoría
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", (categoria_nombre,))
            cat_id = c.lastrowid
            
            # Agregar productos de esta categoría
            for nombre, descripcion, imagen, opciones in productos_list:
                c.execute("""
                INSERT INTO productos (categoria_id, nombre, descripcion, imagen)
                VALUES (?, ?, ?, ?)
                """, (cat_id, nombre, descripcion, imagen))
                
                prod_id = c.lastrowid
                
                # Agregar opciones (precios)
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
    return render_template("menu.html",
                           categorias=categorias,
                           productos=productos,
                           opciones=opciones)


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
    # Verificar autenticación
    if not session.get("admin_logged_in"):
        return redirect("/login")
    
    if request.method == "POST":
        action = request.form.get("action")
        conn = db()
        c = conn.cursor()
        
        try:
            # AGREGAR producto
            if action == "add":
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                categoria_id = request.form.get("categoria_id", None)
                
                imagen = request.files.get("imagen")
                filename = "default.jpg"
                
                if imagen and imagen.filename:
                    filename = secure_filename(imagen.filename)
                    imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                
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
            
            # EDITAR producto
            elif action == "edit":
                producto_id = request.form.get("producto_id")
                nombre = request.form.get("nombre", "")
                descripcion = request.form.get("descripcion", "")
                precio = request.form.get("precio", 0)
                
                # Procesar imagen si se carga una nueva
                imagen = request.files.get("imagen")
                if imagen and imagen.filename:
                    filename = secure_filename(imagen.filename)
                    imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                    c.execute("""
                    UPDATE productos SET nombre = ?, descripcion = ?, imagen = ? WHERE id = ?
                    """, (nombre, descripcion, filename, producto_id))
                else:
                    # Si no se carga imagen, solo actualiza nombre y descripción
                    c.execute("""
                    UPDATE productos SET nombre = ?, descripcion = ? WHERE id = ?
                    """, (nombre, descripcion, producto_id))
                
                c.execute("""
                UPDATE opciones SET precio = ? WHERE producto_id = ?
                """, (int(precio), producto_id))
                
                conn.commit()
            
            # ELIMINAR producto
            elif action == "delete":
                producto_id = request.form.get("producto_id")
                
                c.execute("DELETE FROM opciones WHERE producto_id = ?", (producto_id,))
                c.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
                
                conn.commit()
        finally:
            conn.close()
        
        return redirect("/editserver")
    
    # GET: mostrar productos
    conn = db()
    c = conn.cursor()
    productos = c.execute("SELECT * FROM productos").fetchall()
    categorias = c.execute("SELECT * FROM categorias").fetchall()
    conn.close()
    return render_template("editserver.html", productos=productos, categorias=categorias)

@app.route("/cargar-productos")
def cargar_productos():
    """Carga los productos iniciales en la BD"""
    conn = db()
    c = conn.cursor()
    
    # Verificar si ya existen productos
    c.execute("SELECT COUNT(*) FROM productos")
    if c.fetchone()[0] > 0:
        conn.close()
        return "Los productos ya fueron cargados", 200
    
    productos_datos = [
        ("Fresas con Crema", "Deliciosas fresas con crema y toppings", "fresas.jpg"),
        ("Cono 1 bola", "Helado en cono de una bola", "cono1.jpg"),
        ("Cono 2 bolas", "Helado en cono de dos bolas", "cono2.jpg"),
        ("Canasta 2 bolas", "Canasta con dos bolas de helado", "canasta2.jpg"),
        ("Canasta 3 bolas", "Canasta con tres bolas de helado", "canasta3.jpg"),
        ("Canasta Frutal", "Canasta frutal especial", "frutal.jpg"),
        ("Oblea Sencilla", "Oblea sencilla con dulce de leche", "oblea1.jpg"),
        ("Oblea con Fresas", "Oblea con fresas y crema", "oblea2.jpg"),
        ("Oblea Especial", "Oblea especial con toppings", "oblea3.jpg"),
    ]
    
    opciones_datos = [
        (1, "Pequeña", 12000),
        (1, "Mediana", 15000),
        (1, "Con Toppings", 17000),
        (1, "Con Helado", 22000),
        (2, "Precio", 3500),
        (3, "Precio", 6000),
        (4, "Precio", 7000),
        (5, "Precio", 9000),
        (6, "Precio", 12000),
        (7, "Precio", 2000),
        (8, "Precio", 5000),
        (9, "Precio", 8000),
    ]
    
    for nombre, descripcion, imagen in productos_datos:
        c.execute("""
        INSERT INTO productos (nombre, descripcion, imagen)
        VALUES (?, ?, ?)
        """, (nombre, descripcion, imagen))
    
    for producto_id, nombre_opcion, precio in opciones_datos:
        c.execute("""
        INSERT INTO opciones (producto_id, nombre_opcion, precio)
        VALUES (?, ?, ?)
        """, (producto_id, nombre_opcion, precio))
    
    conn.commit()
    conn.close()
    return "✅ Productos cargados exitosamente en la BD", 200

@app.route("/cargar-menu-productos")
def cargar_menu_productos():
    """Carga los productos del menú en la BD de forma segura"""
    conn = db()
    c = conn.cursor()
    
    # Verificar si ya existen productos del menú
    c.execute("SELECT COUNT(*) FROM productos WHERE nombre LIKE '%Fresas%' OR nombre LIKE '%Cono%'")
    if c.fetchone()[0] > 0:
        conn.close()
        return "Los productos del menú ya fueron cargados", 200
    
    # Crear categorías si no existen
    categorias = {
        "Fresas con Crema": [
            ("Fresas con Crema - Pequeña", "Salsas: Arequipe, Chocolate, Leche condensada, Mermelada de fresa. Toppings: Oreo-maní, Leche en polvo, Chocodisk-piazza, Gomitas-masmelos, Lluvia de chocolate, Choc melo-gusanitos, Chocorramo-masmelos", "fresas.jpg", [("Pequeña", 12000), ("Mediana", 15000), ("Con Toppings", 17000), ("Con Helado", 22000)]),
        ],
        "Helados, Copas y Ensaladas": [
            ("Cono 1 bola", "Helado en cono de una bola", "cono1.jpg", [("Precio", 3500)]),
            ("Cono 2 bolas", "Helado en cono de dos bolas", "cono2.jpg", [("Precio", 6000)]),
            ("Canasta 2 bolas", "Canasta con dos bolas de helado", "canasta2.jpg", [("Precio", 7000)]),
            ("Canasta 3 bolas", "Canasta con tres bolas de helado", "canasta3.jpg", [("Precio", 9000)]),
            ("Canasta Frutal", "Canasta frutal especial", "frutal.jpg", [("Precio", 12000)]),
        ],
        "Obleas": [
            ("Oblea Sencilla", "Oblea sencilla con dulce de leche", "oblea1.jpg", [("Precio", 2000)]),
            ("Oblea con Fresas", "Oblea con fresas y crema", "oblea2.jpg", [("Precio", 5000)]),
            ("Oblea Especial", "Oblea especial con toppings", "oblea3.jpg", [("Precio", 8000)]),
        ]
    }
    
    for categoria_nombre, productos_list in categorias.items():
        # Crear o obtener categoría
        c.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria_nombre,))
        result = c.fetchone()
        if result:
            cat_id = result[0]
        else:
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", (categoria_nombre,))
            cat_id = c.lastrowid
        
        # Agregar productos de esta categoría
        for nombre, descripcion, imagen, opciones in productos_list:
            c.execute("""
            INSERT INTO productos (categoria_id, nombre, descripcion, imagen)
            VALUES (?, ?, ?, ?)
            """, (cat_id, nombre, descripcion, imagen))
            
            prod_id = c.lastrowid
            
            # Agregar opciones (precios)
            for nombre_opcion, precio in opciones:
                c.execute("""
                INSERT INTO opciones (producto_id, nombre_opcion, precio)
                VALUES (?, ?, ?)
                """, (prod_id, nombre_opcion, precio))
    
    conn.commit()
    conn.close()
    return "✅ Productos del menú cargados en la BD exitosamente", 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
