
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error
from db import obtener_conexion

app = Flask(__name__)
app.secret_key = "centinela_clave_2026"


# PAGINA PRINCIPAL
@app.route('/')
def inicio():
    return render_template('index.html')


# CREAR CUENTA
@app.route('/crear_cuenta')
def crear_cuenta():
    return render_template('crear_cuenta.html')


# INICIAR SESION
@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM usuarios WHERE email=%s",
                (email,)
            )

            usuario = cursor.fetchone()

            cursor.close()
            conexion.close()

            if usuario and check_password_hash(usuario['password'], password):
                session['usuario'] = usuario['nombre']
                flash('Bienvenido a Centinela Digital.', 'success')
                return redirect(url_for('inicio'))

            flash('Correo o contraseña incorrectos.', 'error')

        except Error:
            flash('No se pudo conectar con la base de datos.', 'error')

    return render_template('inicio_de_sesion.html')


# CERRAR SESION
@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('inicio'))


# PAGINAS ADICIONALES
@app.route('/reportes')
def pagina_reportes():
    return render_template('reportes.html')


@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')


@app.route('/contactos')
def contactos():
    return render_template('contactos.html')

@app.route('/informacion')
def informacion():
    return render_template('informacion.html')


# REGISTRAR USUARIOS
@app.route('/register', methods=['POST'])
def register():

    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    if not nombre or not email or not password:
        flash('Completa todos los campos.', 'error')
        return redirect(url_for('crear_cuenta'))

    if password != confirm:
        flash('Las contraseñas no coinciden.', 'error')
        return redirect(url_for('crear_cuenta'))

    if (len(password) < 6 or
        not any(c.isdigit() for c in password) or
        not any(not c.isalnum() for c in password)):

        flash('La contraseña necesita 6 caracteres, un número y un símbolo.', 'error')
        return redirect(url_for('crear_cuenta'))

    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(150) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            )
        """)

        cursor.execute(
            "SELECT id FROM usuarios WHERE email=%s",
            (email,)
        )

        if cursor.fetchone():
            flash('Este correo ya está registrado.', 'error')
            return redirect(url_for('crear_cuenta'))

        clave_segura = generate_password_hash(password)

        cursor.execute(
            """INSERT INTO usuarios (nombre, email, password)
            VALUES (%s, %s, %s)""",
            (nombre, email, clave_segura)
        )

        conexion.commit()

        flash('¡Tu cuenta se creó correctamente!', 'success')
        return redirect(url_for('iniciar_sesion'))

    except Error:
        if conexion:
            conexion.rollback()

        flash('No se pudo crear la cuenta. Revisa la base de datos.', 'error')
        return redirect(url_for('crear_cuenta'))

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# CONSULTAR Y GUARDAR REPORTES
@app.route('/api/reportes', methods=['GET', 'POST'])
def api_reportes():

    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        # CONSULTAR REPORTES
        if request.method == 'GET':
            cursor.execute(
                "SELECT * FROM reportes ORDER BY id DESC"
            )

            return jsonify(cursor.fetchall())

        # GUARDAR REPORTES
        datos = request.get_json(silent=True) or request.form

        titulo = datos.get('titulo', '').strip()
        autor = datos.get('autor', '').strip()
        descripcion = datos.get('descripcion', '').strip()

        if not titulo or not autor or not descripcion:
            return jsonify({
                'error': 'Completa todos los campos.'
            }), 400

        cursor.execute(
            """INSERT INTO reportes (titulo, autor, descripcion)
            VALUES (%s, %s, %s)""",
            (titulo, autor, descripcion)
        )

        conexion.commit()

        return jsonify({
            'mensaje': 'Reporte guardado correctamente.'
        }), 201

    except Error:
        if conexion:
            conexion.rollback()

        return jsonify({
            'error': 'No se pudo consultar o guardar el reporte.'
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conexion and conexion.is_connected():
            conexion.close()


# EJECUTAR APLICACION
if __name__ == '__main__':
    app.run(debug=True)