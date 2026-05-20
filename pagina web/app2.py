import requests
import os
import uuid
from functools import wraps
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)

#App configuration
app = Flask(__name__)
app.secret_key = 'localhero_super_secret_key_2024'

API_URL = "http://127.0.0.1:5000/api"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "img")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
EXTENSIONES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "gif"}


@app.route("/api/subir-imagen-perfil", methods=["POST"])
def subir_imagen_perfil():
    if "imagen" not in request.files:
        return jsonify({"mensaje": "No se recibió ninguna imagen"}), 400
    archivo = request.files["imagen"]
    if not archivo.filename:
        return jsonify({"mensaje": "Archivo vacío"}), 400
    ext = archivo.filename.rsplit(".", 1)[-1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        return jsonify({"mensaje": "Formato no permitido. Usa jpg, png o webp"}), 400
    nombre = f"perfil_{uuid.uuid4().hex}.{ext}"
    archivo.save(os.path.join(UPLOAD_FOLDER, nombre))
    return jsonify({"nombre_archivo": f"/static/img/{nombre}"}), 200


#Decorators

def requiere_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('usuario_id'):
            flash("Debes de estar registar con la sesion iniciada para entrar a la pagina.")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrapper


def requiere_propietario(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('usuario_id'):
            flash("Debes de estar registar con la sesion iniciada para entrar a la pagina.")
            return redirect(url_for('login_page'))
        if session.get('rol') != 'propietario':
            flash("Esta seccion es exclusiva para propietarios.")
            return redirect(url_for('principal'))
        return f(*args, **kwargs)
    return wrapper


#login, register, logout

@app.route("/")
def login_page():
    if session.get('usuario_id'):
        if session.get('rol') == 'propietario':
            return redirect(url_for('panel_propietario'))
        return redirect(url_for('principal'))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    correo = request.form.get("correo", "").strip()
    clave  = request.form.get("password", "")

    #Basic validation
    if not correo or not clave:
        return jsonify({"mensaje": "Porfavor rellena todos los campos."}), 400

    payload = {"correo": correo, "password": clave}

    try:
        r = requests.post(f"{API_URL}/login", json=payload, timeout=5)

        if r.status_code == 200:
            datos = r.json()

            # Store user data in session
            session['usuario_id'] = datos['usuario']['id']
            session['nombre']     = datos['usuario']['nombre']
            session['rol']        = datos['usuario']['rol']

            # Redirect based on role
            if datos['usuario']['rol'] == 'propietario':
                return redirect(url_for('panel_propietario'))
            return redirect(url_for('principal'))

        try:
            api_msg = r.json().get("mensaje", "")
        except Exception:
            api_msg = ""

        status_messages = {
            400: api_msg or "Datos faltantes o inválidos.",
            401: api_msg or "Contraseña incorrecta.",
            404: api_msg or "No se encontró ninguna cuenta con ese correo electrónico.",
        }
        msg = status_messages.get(r.status_code, api_msg or "Error al iniciar sesión.")
        return jsonify({"mensaje": msg}), r.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"mensaje": "No se puede conectar con el servidor de datos. Inténtalo de nuevo más tarde."}), 503

    except Exception as e:
        print(f"[login] Unexpected error: {e}")
        return jsonify({"mensaje": "Error inesperado. Por favor, inténtalo de nuevo."}), 500


@app.route("/registro")
def registro_page():

    if session.get('usuario_id'):
        return redirect(url_for('principal'))
    return render_template("registro.html")


@app.route("/registro_proceso", methods=["POST"])
def registrar():

    correo   = request.form.get("correo", "").strip()
    password = request.form.get("password", "")

    payload = {
        "usuario":   request.form.get("usuario"),
        "nombre":    request.form.get("nombre"),
        "apellido":  request.form.get("apellido"),
        "correo":    correo,
        "password":  password,
        "telefono":  request.form.get("telefono"),
        "direccion": request.form.get("direccion"),
        "rol":       "usuario"
    }

    try:
        r = requests.post(f"{API_URL}/usuarios", json=payload, timeout=5)

        if r.status_code == 201:
            # Registration succeeded — auto-login so the user doesn't have
            # to fill in their credentials a second time.
            try:
                r_login = requests.post(
                    f"{API_URL}/login",
                    json={"correo": correo, "password": password},
                    timeout=5
                )
                if r_login.status_code == 200:
                    datos = r_login.json()
                    session['usuario_id'] = datos['usuario']['id']
                    session['nombre']     = datos['usuario']['nombre']
                    session['rol']        = datos['usuario']['rol']
                    return redirect(url_for('principal'))
            except Exception as e:
                print(f"[registrar] Auto-login failed: {e}")

            # Auto-login failed for some reason — fall back to login page
            flash("Cuenta creada. Por favor, inicia sesión para continuar.")
            return redirect(url_for('login_page'))

        error_data = r.json()
        flash(error_data.get("mensaje", "Error en el registro."))
        return redirect(url_for('registro_page'))

    except Exception as e:
        print(f"[registrar] Error: {e}")
        flash("El servidor de datos no responde.")
        return redirect(url_for('registro_page'))


@app.route("/registro-propietario")
def registro_propietario_page():

    if session.get('usuario_id'):
        return redirect(url_for('panel_propietario'))
    return render_template("registro_propietario.html")


@app.route("/logout")
def logout():

    session.clear()
    flash("Has cerrado sesión correctamente.")
    return redirect(url_for('login_page'))


#users routes protected

@app.route("/principal")
@requiere_login
def principal():

    try:
        r = requests.get(f"{API_URL}/tiendas", timeout=5)
        tiendas = r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"[principal] API error: {e}")
        tiendas = []

    return render_template("principal.html", tiendas=tiendas)


@app.route("/perfil")
@requiere_login
def perfil():
    try:
        r = requests.get(f"{API_URL}/usuarios/{session['usuario_id']}", timeout=5)

        if r.status_code != 200:
            flash("No se pudo cargar tu perfil.")
            return redirect(url_for('login_page'))

        datos = r.json()

    except Exception as e:
        print(f"[perfil] Error: {e}")
        flash("Error de conexión al cargar el perfil.")
        return redirect(url_for('login_page'))

    return render_template("perfil.html", usuario=datos)


@app.route("/tienda/<int:id_tienda>")
@requiere_login
def tienda(id_tienda):

    try:
        r_tienda = requests.get(f"{API_URL}/tiendas/{id_tienda}", timeout=5)
        datos_tienda = r_tienda.json() if r_tienda.status_code == 200 else None

        r_prod = requests.get(f"{API_URL}/productos/tienda/{id_tienda}", timeout=5)
        lista_productos = r_prod.json() if r_prod.status_code == 200 else []

        if not datos_tienda:
            return "Tienda no encontrada", 404

        return render_template(
            "tienda.html",
            tienda=datos_tienda,
            productos=lista_productos
        )

    except Exception as e:
        print(f"[tienda] Error: {e}")
        return redirect(url_for('principal'))


@app.route("/pedidos")
@requiere_login
def pedidos():

    try:
        r = requests.get(f"{API_URL}/pedidos/{session['usuario_id']}", timeout=5)
        mis_pedidos = r.json() if r.status_code == 200 else []
    except Exception:
        mis_pedidos = []

    return render_template("mis_pedidos.html", pedidos=mis_pedidos)


@app.route("/categorias")
@requiere_login
def categorias():

    try:
        r = requests.get(f"{API_URL}/categorias", timeout=5)
        categorias_lista = r.json() if r.status_code == 200 else []
    except Exception as e:
        print(f"[categorias] Error: {e}")
        categorias_lista = []

    return render_template("categorias.html", categorias=categorias_lista)


@app.route("/actualizar_perfil", methods=["POST"])
@requiere_login
def actualizar_perfil():

    payload = {
        "usuario":   request.form.get("usuario", "").strip(),
        "telefono":  request.form.get("telefono", "").strip(),
        "direccion": request.form.get("direccion", "").strip(),
    }

    imagen = request.form.get("imagen_perfil_nombre", "").strip()
    if imagen:
        payload["imagen_perfil"] = imagen

    try:
        r = requests.put(
            f"{API_URL}/usuarios/{session['usuario_id']}",
            json=payload,
            timeout=5
        )

        if r.status_code == 200:
            # Keep session name in sync if username changed
            if payload["usuario"]:
                session["nombre"] = payload["usuario"]
            flash("Perfil actualizado correctamente.")
        else:
            try:
                msg = r.json().get("mensaje", "Error al actualizar.")
            except Exception:
                msg = "Error al actualizar."
            flash(msg)

    except Exception as e:
        print(f"[actualizar_perfil] Error: {e}")
        flash("Error de conexión al guardar los cambios.")

    return redirect(url_for("perfil"))


@app.route("/carrito/confirmar", methods=["POST"])
@requiere_login
def confirmar_pedido():

    data     = request.get_json()
    productos = data.get("productos", [])

    if not productos:
        return jsonify({"mensaje": "El carrito está vacío."}), 400

    errores = []

    for item in productos:
        try:
            # peso_kg is the weight of one unit of this product.
            # cantidad is how many units the user ordered.
            # The total weight saved = peso_kg × cantidad.
            peso_unitario = float(item.get("peso_kg") or 0)
            cantidad      = int(item.get("cantidad") or 1)
            peso_total    = peso_unitario * cantidad if peso_unitario > 0 else cantidad

            payload = {
                "id_usuario":  session['usuario_id'],
                "id_producto": item.get("id_producto"),
                "peso":        peso_total
            }
            r = requests.post(f"{API_URL}/salvar", json=payload, timeout=5)

            if r.status_code != 201:
                errores.append(item.get("nombre", "producto"))

        except Exception:
            errores.append(item.get("nombre", "producto"))

    if errores:
        return jsonify({"mensaje": f"Error al guardar: {', '.join(errores)}"}), 500

    return jsonify({"mensaje": "Pedido realizado correctamente."}), 200


#Owner routes protected
@app.route("/propietario/panel")
@requiere_propietario
def panel_propietario():
    """
    GET /propietario/panel
    Shows the owner's management dashboard.
    Passes the owner's name from the session to the template.
    """
    return render_template(
        "panel_propietario.html",
        nombre=session.get('nombre', 'Propietario')
    )


@app.route("/propietario/crear-tienda")
@requiere_propietario
def crear_tienda_page():
    """
    GET /propietario/crear-tienda
    Shows the store creation form for owners who don't have a store yet.
    """
    return render_template("crear_tienda.html")


#accessible without login

@app.route('/contacto')
def contacto():
    return render_template("contacto.html")


@app.route('/preguntas-frecuentes')
def preguntas_frecuentes():
    return render_template("preguntas_frecuentes.html")


@app.route('/envios')
def envios():
    return render_template("envios.html")


@app.route('/politica-privacidad')
def politica_privacidad():
    return render_template("politica_privacidad.html")


@app.route('/terminos-condiciones')
def terminos_condiciones():
    return render_template("terminos_condiciones.html")



if __name__ == "__main__":
    app.run(debug=True, port=8000)