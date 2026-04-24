from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/registro")
def registro_page():
    return render_template("registro.html")

@app.route("/principal")
def principal():
    return render_template("principal.html")

@app.route('/perfil')
def perfil():
    usuario = {
        "nombre": "Juan Pérez",
        "email": "juan@email.com",
        "direccion": "Calle Falsa 123",
        "codigo_postal": "28001"
    }
    return render_template("perfil.html", usuario=usuario)


@app.route('/pedidos')
def pedidos():
    return render_template("mis_pedidos.html")

@app.route('/tienda')
def tienda():
    tienda = {
        "nombre": "Tienda Verde",
        "direccion": "Calle Mayor 12",
        "km": "1.2 km"
    }
    return render_template("tienda.html", tienda=tienda)

@app.route('/perfil/editar')
def editar_perfil():
    return render_template("editar_perfil.html")

# ================= PÁGINAS DEL FOOTER =================

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

# ======================================================

                                                  #MIRAR DE AQUI A ABAJO MUY BIEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEN

                                                  #ESTO SE USA PARA NAVEGACION CON LOGICA(DATOS)
@app.route("/login", methods=["POST"])
def login():
    usuario = request.form["usuario"]
    clave = request.form["clave"]

    #AQUI SUPONGO QUE HABRIA QUE HACER UNA VERIFICACION DE USUARIO Y CONTRASEÑA

    return redirect("/principal")

@app.route("/registro", methods=["POST"])
def registrar():
    usuario = request.form["usuario"]
    correo = request.form["correo"]
    clave = request.form["clave"]

    # aquí guardarías en BD

    return redirect("/principal")

if __name__ == "__main__":
    app.run(debug=True)
