from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import bcrypt
import os
import uuid

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": "http://127.0.0.1:8000"
    }
})

# Carpeta donde se guardan las imágenes subidas
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "img")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "gif"}

def extension_permitida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS

@app.route("/api/subir-imagen-perfil", methods=["POST"])
def subir_imagen_perfil():
    if "imagen" not in request.files:
        return jsonify({"mensaje": "No se recibió ninguna imagen"}), 400
    archivo = request.files["imagen"]
    if not archivo.filename or not extension_permitida(archivo.filename):
        return jsonify({"mensaje": "Formato no permitido. Usa jpg, png o webp"}), 400
    ext = archivo.filename.rsplit(".", 1)[1].lower()
    nombre = f"perfil_{uuid.uuid4().hex}.{ext}"
    archivo.save(os.path.join(UPLOAD_FOLDER, nombre))
    return jsonify({"nombre_archivo": f"/static/img/{nombre}"}), 200

#AWS RDS MYSQL connection

def conectar_db():
    return pymysql.connect(
        host="localherobbdd.c9luijiopxtf.us-east-1.rds.amazonaws.com",
        user="admin",
        password="2000fernandez",
        database="localherobbdd",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

# 1. user registration

@app.route("/api/usuarios", methods=["POST"])
def registro_usuario():

    db = None

    try:
        datos = request.get_json()

        password = datos.get("password")

        if not password:
            return jsonify({
                "status": "error",
                "mensaje": "Falta contraseña"
            }), 400

        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        db = conectar_db()
        cursor = db.cursor()

        rol = datos.get("rol", "usuario")
        if rol not in ("usuario", "propietario"):
            rol = "usuario"

        cursor.execute("""
            INSERT INTO usuarios
            (
                usuario,
                nombre,
                apellido,
                correo,
                contrasena_hash,
                telefono,
                direccion,
                rol
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos.get("usuario"),
            datos.get("nombre"),
            datos.get("apellido"),
            datos.get("correo"),
            password_hash,
            datos.get("telefono"),
            datos.get("direccion"),
            rol
        ))

        db.commit()

        return jsonify({
            "status": "success",
            "mensaje": "Usuario creado correctamente"
        }), 201

    except pymysql.err.IntegrityError:
        return jsonify({
            "status": "error",
            "mensaje": "El usuario o correo ya existen"
        }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

    finally:
        if db:
            db.close()

# 2. login

@app.post("/api/login")
def api_login():

    db = None

    try:
        datos = request.get_json()

        correo = datos.get("correo")
        password = datos.get("password")

        if not correo or not password:
            return jsonify({
                "status": "error",
                "mensaje": "Faltan datos"
            }), 400

        db = conectar_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                id_usuario,
                usuario,
                nombre,
                correo,
                contrasena_hash,
                rol
            FROM usuarios
            WHERE correo = %s
        """, (correo,))

        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({
                "status": "error",
                "mensaje": "Usuario no encontrado"
            }), 404

        if bcrypt.checkpw(
            password.encode(),
            usuario["contrasena_hash"].encode()
        ):

            return jsonify({
                "status": "success",
                "usuario": {
                    "id": usuario["id_usuario"],
                    "usuario": usuario["usuario"],
                    "nombre": usuario["nombre"],
                    "rol": usuario["rol"]
                }
            }), 200

        return jsonify({
            "status": "error",
            "mensaje": "Contraseña incorrecta"
        }), 401

    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

    finally:
        if db:
            db.close()

# 3. products

@app.get("/api/productos")
def get_productos():

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM productos
        WHERE disponible = 1
    """)

    productos = cursor.fetchall()

    db.close()

    return jsonify(productos)

# 4. product by id

@app.get("/api/productos/<int:id>")
def get_producto(id):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM productos
        WHERE id_producto = %s
    """, (id,))

    producto = cursor.fetchone()

    db.close()

    if producto:
        return jsonify(producto)

    return jsonify({
        "error": "Producto no encontrado"
    }), 404

# 5. stores

@app.get("/api/tiendas")
def get_tiendas():

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            id_tienda,
            nombre_tienda,
            direccion_tienda,
            ciudad,
            latitud,
            longitud,
            imagenes,
            horario
        FROM tiendas
    """)

    tiendas = cursor.fetchall()

    db.close()

    return jsonify(tiendas)

# 6. store by id

@app.get("/api/tiendas/<int:id>")
def get_tienda_detalle(id):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT *
        FROM tiendas
        WHERE id_tienda = %s
    """, (id,))

    node = cursor.fetchone()

    db.close()

    if node:
        return jsonify(node)

    return jsonify({
        "error": "Tienda no encontrada"
    }), 404

# stores by owner

@app.get("/api/tiendas/propietario/<int:id_propietario>")
def get_tiendas_propietario(id_propietario):
    db = conectar_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tiendas WHERE propietario_id = %s", (id_propietario,))
    tienda = cursor.fetchone()
    db.close()
    if not tienda:
        return jsonify({"error": "Sin tienda"}), 404
    return jsonify(tienda)

# 7. products from a store

@app.get("/api/productos/tienda/<int:id_tienda>")
def get_productos_tienda(id_tienda):

    todos = request.args.get("todos") == "1"
    db = conectar_db()
    cursor = db.cursor()

    if todos:
        cursor.execute("""
            SELECT
                id_producto, tienda_id, nombre, descripcion,
                imagen_producto, peso_kg, fecha_caducidad,
                disponible, fecha_alta, stock
            FROM productos
            WHERE tienda_id = %s
        """, (id_tienda,))
    else:
        cursor.execute("""
            SELECT
                id_producto, tienda_id, nombre, descripcion,
                imagen_producto, peso_kg, fecha_caducidad,
                disponible, fecha_alta, stock
            FROM productos
            WHERE tienda_id = %s AND disponible = 1
        """, (id_tienda,))

    productos = cursor.fetchall()
    db.close()
    return jsonify(productos)

# 8. confirm order / save products

@app.post("/api/salvar")
def salvar_producto():

    db = None

    try:
        datos = request.get_json()

        usuario_id = datos.get("id_usuario")
        producto_id = datos.get("id_producto")
        peso = datos.get("peso", 1)

        if not usuario_id or not producto_id:
            return jsonify({
                "mensaje": "Faltan datos"
            }), 400

        db = conectar_db()
        cursor = db.cursor()

        # check that the product exists and has stock

        cursor.execute("""
            SELECT disponible, stock
            FROM productos
            WHERE id_producto = %s
        """, (producto_id,))

        producto = cursor.fetchone()

        if not producto:
            return jsonify({"mensaje": "Producto no encontrado"}), 404

        if producto["disponible"] == 0:
            return jsonify({"mensaje": "Producto ya no disponible"}), 400

        # Si no tiene columna stock definida, tratar como stock = 1
        stock_actual = producto["stock"] if producto.get("stock") is not None else 1

        if stock_actual <= 0:
            return jsonify({"mensaje": "Producto sin stock disponible"}), 400

        # insert into saved

        cursor.execute("""
            INSERT INTO salvados
            (usuario_id, producto_id, peso_salvado, estado)
            VALUES (%s, %s, %s, 'activo')
        """, (usuario_id, producto_id, peso))

        nuevo_stock = stock_actual - 1

        cursor.execute("""
            UPDATE productos
            SET stock = %s,
                disponible = %s
            WHERE id_producto = %s
        """, (nuevo_stock, 1 if nuevo_stock > 0 else 0, producto_id))

        db.commit()

        return jsonify({
            "mensaje": "Producto salvado correctamente"
        }), 201

    except Exception as e:

        return jsonify({
            "mensaje": str(e)
        }), 500

    finally:
        if db:
            db.close()

# 9. user profile

@app.get("/api/usuarios/<int:id>")
def get_usuario_detalle(id):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            usuario,
            nombre,
            apellido,
            correo,
            contrasena_hash,
            telefono,
            direccion,
            imagen_perfil,
            rol
        FROM usuarios
        WHERE id_usuario = %s
    """, (id,))

    usuario = cursor.fetchone()

    if not usuario:
        db.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute("""
        SELECT COALESCE(SUM(peso_salvado), 0) AS total_kg
        FROM salvados
        WHERE usuario_id = %s
    """, (id,))

    kg = cursor.fetchone()

    db.close()

    usuario["total_kg"] = kg["total_kg"]

    return jsonify(usuario)

# 10. user orders

@app.get("/api/pedidos/<int:id_usuario>")
def get_pedidos_usuario(id_usuario):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            s.id_salvado,
            s.fecha,
            s.estado,
            s.peso_salvado,

            p.nombre AS producto_nombre,
            p.imagen_producto,

            t.nombre_tienda

        FROM salvados s

        JOIN productos p
            ON s.producto_id = p.id_producto

        JOIN tiendas t
            ON p.tienda_id = t.id_tienda

        WHERE s.usuario_id = %s

        ORDER BY s.fecha DESC
    """, (id_usuario,))

    pedidos = cursor.fetchall()

    db.close()

    return jsonify(pedidos)


@app.get("/api/pedidos/tienda/<int:id_tienda>")
def get_pedidos_tienda(id_tienda):
    db = conectar_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            s.id_salvado,
            s.fecha,
            s.peso_salvado,
            s.estado,
            p.nombre  AS producto_nombre,
            u.nombre  AS cliente_nombre,
            u.telefono AS cliente_telefono
        FROM salvados s
        JOIN productos p ON s.producto_id = p.id_producto
        JOIN usuarios  u ON s.usuario_id  = u.id_usuario
        WHERE p.tienda_id = %s AND s.estado = 'activo'
        ORDER BY s.fecha DESC
    """, (id_tienda,))
    pedidos = cursor.fetchall()
    db.close()
    return jsonify(pedidos)


@app.put("/api/salvados/<int:id>/confirmar")
def confirmar_recogida(id):
    db = None
    try:
        db = conectar_db()
        cursor = db.cursor()
        cursor.execute("UPDATE salvados SET estado = 'recogido' WHERE id_salvado = %s", (id,))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({"mensaje": "Pedido no encontrado"}), 404
        return jsonify({"mensaje": "Recogida confirmada"}), 200
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 500
    finally:
        if db:
            db.close()



@app.get("/api/usuarios/<int:id>/kg-total")
def get_kg_total(id):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(peso_salvado), 0) AS total_kg
        FROM salvados
        WHERE usuario_id = %s
    """, (id,))

    result = cursor.fetchone()
    db.close()

    return jsonify(result)

@app.route("/api/tiendas", methods=["POST"])
def crear_tienda():
    db = None
    try:
        data = request.get_json()

        if not data.get("nombre_tienda") or not data.get("direccion_tienda") or not data.get("ciudad"):
            return jsonify({"mensaje": "Faltan campos obligatorios (nombre, dirección, ciudad)"}), 400

        db = conectar_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO tiendas
            (propietario_id, nombre_tienda, correo_tienda, telefono_tienda,
             direccion_tienda, ciudad, latitud, longitud, imagenes, horario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("propietario_id"),
            data.get("nombre_tienda"),
            data.get("correo_tienda"),
            data.get("telefono"),
            data.get("direccion_tienda"),
            data.get("ciudad"),
            data.get("latitud"),
            data.get("longitud"),
            data.get("imagenes", "[]"),
            data.get("horario")
        ))

        db.commit()

        return jsonify({"mensaje": "Tienda creada", "id_tienda": cursor.lastrowid}), 201

    except Exception as e:
        return jsonify({"mensaje": str(e)}), 500

    finally:
        if db:
            db.close()

@app.route("/api/productos", methods=["POST"])
def crear_producto():
    db = None
    try:
        data = request.get_json()

        if not data.get("tienda_id") or not data.get("nombre"):
            return jsonify({"mensaje": "Faltan campos obligatorios (tienda_id, nombre)"}), 400

        db = conectar_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO productos
            (tienda_id, nombre, descripcion, imagen_producto,
             peso_kg, fecha_caducidad, disponible, stock)
            VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
        """, (
            data.get("tienda_id"),
            data.get("nombre"),
            data.get("descripcion"),
            data.get("imagen_producto"),
            data.get("peso_kg"),
            data.get("fecha_caducidad"),
            data.get("stock", 1)
        ))

        db.commit()

        return jsonify({"mensaje": "Producto creado", "id_producto": cursor.lastrowid}), 201

    except Exception as e:
        return jsonify({"mensaje": str(e)}), 500

    finally:
        if db:
            db.close()

# categories - get all

@app.get("/api/categorias")
def get_categorias():

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id_categoria, nombre
        FROM categorias
        ORDER BY nombre
    """)

    categorias = cursor.fetchall()
    db.close()

    return jsonify(categorias)


# stores by category

@app.get("/api/tiendas/categoria/<int:id_categoria>")
def get_tiendas_por_categoria(id_categoria):

    db = conectar_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT DISTINCT
            t.id_tienda,
            t.nombre_tienda,
            t.direccion_tienda,
            t.ciudad,
            t.horario,
            t.latitud,
            t.longitud,
            t.imagenes
        FROM tiendas t
        JOIN productos p
            ON p.tienda_id = t.id_tienda
        JOIN producto_categoria pc
            ON pc.producto_id = p.id_producto
        WHERE pc.categoria_id = %s
          AND p.disponible = 1
    """, (id_categoria,))

    tiendas = cursor.fetchall()
    db.close()

    return jsonify(tiendas)


# update user profile - put

@app.put("/api/usuarios/<int:id>")
def actualizar_usuario(id):

    db = None

    try:
        datos = request.get_json()

        if not datos:
            return jsonify({
                "status": "error",
                "mensaje": "No se recibieron datos"
            }), 400

        campos = []
        valores = []

        if "usuario" in datos and datos["usuario"]:
            campos.append("usuario = %s")
            valores.append(datos["usuario"])

        if "telefono" in datos:
            campos.append("telefono = %s")
            valores.append(datos["telefono"])

        if "direccion" in datos:
            campos.append("direccion = %s")
            valores.append(datos["direccion"])

        if not campos:
            return jsonify({
                "status": "error",
                "mensaje": "No hay campos para actualizar"
            }), 400

        valores.append(id)

        db = conectar_db()
        cursor = db.cursor()

        cursor.execute(f"""
            UPDATE usuarios
            SET {', '.join(campos)}
            WHERE id_usuario = %s
        """, tuple(valores))

        db.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "status": "error",
                "mensaje": "Usuario no encontrado"
            }), 404

        return jsonify({
            "status": "success",
            "mensaje": "Perfil actualizado correctamente"
        }), 200

    except pymysql.err.IntegrityError:
        return jsonify({
            "status": "error",
            "mensaje": "El nombre de usuario ya está en uso"
        }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": str(e)
        }), 500

    finally:
        if db:
            db.close()

# start server

if __name__ == "__main__":
    app.run(debug=True, port=5000)