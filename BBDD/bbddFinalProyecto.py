import sqlite3

#Conectar si no existe, se crea
conexion = sqlite3.connect("bbdd_proyecto.db")
cursor = conexion.cursor() 

#rol(usuarios)'usuario','propietario','admin'
#estado(salvados) 'activo','recogido','cancelado'
cursor.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL, 
        contrasena_hash TEXT NOT NULL,
        telefono TEXT NOT NULL,
        direccion TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('usuario','propietario','admin')) NOT NULL DEFAULT 'usuario'          
    
    CREATE TABLE IF NOT EXISTS tiendas (
        id_tienda INTEGER PRIMARY KEY AUTOINCREMENT,
        propietario_id INTEGER NOT NULL,
        nombre_tienda TEXT NOT NULL,
        correo_tienda TEXT UNIQUE,
        telefono_tienda TEXT,
        direccion_tienda TEXT,
        imagenes TEXT,
        ciudad TEXT,
        horario TEXT,
        FOREIGN KEY (propietario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
        );

    CREATE TABLE IF NOT EXISTS categorias (
        id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS productos (
        id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        peso_kg REAL CHECK(peso_kg >= 0),                              
        fecha_caducidad DATE,
        disponible INTEGER CHECK(disponible IN (0,1)) DEFAULT 1,
        fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tienda_id) REFERENCES tiendas(id_tienda) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS producto_categoria (
        producto_id INTEGER NOT NULL,
        categoria_id INTEGER NOT NULL,
        PRIMARY KEY (producto_id, categoria_id),
        FOREIGN KEY (producto_id) REFERENCES productos(id_producto) ON DELETE CASCADE,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id_categoria) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS valoraciones (
        id_valoracion INTEGER PRIMARY KEY AUTOINCREMENT,
        tienda_id INTEGER NOT NULL,
        usuario_id INTEGER,
        puntuacion INTEGER CHECK(puntuacion BETWEEN 1 AND 5),
        comentario TEXT,
        FOREIGN KEY (tienda_id) REFERENCES tiendas(id_tienda) ON DELETE CASCADE,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario) ON DELETE SET NULL,
        UNIQUE (usuario_id, tienda_id)
    );
    
    CREATE TABLE IF NOT EXISTS salvados (
        id_salvado INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        estado TEXT CHECK(estado IN ('activo','recogido','cancelado')) DEFAULT 'activo',
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id_producto) ON DELETE CASCADE,
        UNIQUE (usuario_id, producto_id)
    );
    """)

conexion.commit()
conexion.close()

print("Base de datos creada correctamente.")
