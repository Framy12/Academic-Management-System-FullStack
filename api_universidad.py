from flask import Flask, jsonify, request, send_file, session 
import pyodbc
from flask_cors import CORS  
import pandas as pd
import io
 
app = Flask(__name__)
CORS(app)  #--(Esto abre la puerta a todos)

# IMPORTANTE: Esto encripta los datos de la sesión.
app.secret_key = 'mi_secreto_super_seguro_utesa'

# --- CONFIGURACIÓN  ---
server = 'DESKTOP-L3KRF2G\SQLEXPRESS'  # Ej: DESKTOP-558\SQLEXPRESS
database = 'GestionEstudiantes' 


def obtener_conexion():
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    return pyodbc.connect(connection_string)

# --- RUTA 1: La página de bienvenida ---
@app.route('/') 
def home():
    return "<h1> ¡Servidor Académico en Línea!</h1><p>Usa /notas/ID para consultar.</p>"

# --- RUTA 2: Consultar Notas (La API Real) ---
# Esto captura el ID que escribas en la URL
@app.route('/notas/<int:id_estudiante>', methods=['GET'])
def consultar_notas(id_estudiante):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # Consultamos tu VISTA
        query = "SELECT * FROM vw_HistorialAcademico WHERE id_estudiante = ?"
        cursor.execute(query, id_estudiante)
        
        columnas = [column[0] for column in cursor.description] # Nombres de las columnas
        filas = cursor.fetchall()
        
        conn.close()

        if filas:
            # Convertimos los datos de SQL a JSON (Diccionario de Python)
            resultados = []
            for fila in filas:
                # Creamos un diccionario { "Materia": "Matemáticas", "Nota": 90 ... }
                dato = dict(zip(columnas, fila))
                resultados.append(dato)
            
            return jsonify({
                "status": "success",
                "estudiante_id": id_estudiante,
                "data": resultados
            })
        else:
            return jsonify({"status": "error", "mensaje": "Estudiante no encontrado"}), 404

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# --- RUTA 3: Inscribir Materia (Recibe datos y Ejecuta SP) ---
@app.route('/inscribir', methods=['POST']) # <--- Fíjate que ahora dice POST
def inscribir_materia():
    try:
        # 1. Recibimos el "Paquete" que envía la página web
        datos_entrada = request.get_json()
        
        # Extraemos las dos piezas que necesitamos
        id_estudiante = datos_entrada['id_estudiante']
        materia = datos_entrada['materia']

        conn = obtener_conexion()
        cursor = conn.cursor()

        # 2. Llamamos a SQL (Igual que en tu script de consola anterior)
        print(f"📝 Intentando inscribir al ID {id_estudiante} en {materia}...")
        
        # Ejecutamos el Stored Procedure
        sql = "EXEC sp_VerificarInscripcion @EstudianteID = ?, @NombreMateria = ?"
        cursor.execute(sql, (id_estudiante, materia))
        
        # 3. Leemos qué respondió el SP (Autorizado o Denegado)
        resultado_sql = cursor.fetchone()
        conn.commit() # ¡IMPORTANTE! Guardar cambios si hubo inserción
        conn.close()

        if resultado_sql:
            mensaje_db = resultado_sql[0] # El texto que devuelve SQL
            
            # Analizamos si fue éxito o error para avisarle al Frontend
            estado = "success" if "AUTORIZADO" in mensaje_db else "error"
            
            return jsonify({
                "status": estado,
                "mensaje": mensaje_db
            })
        else:
            return jsonify({"status": "error", "mensaje": "La base de datos no respondió nada."})

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    
# --- RUTA 4: Obtener Lista de Materias (Para el Dropdown) ---
@app.route('/materias', methods=['GET'])
def listar_materias():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # Solo necesitamos el ID y el Nombre para la lista
        cursor.execute("SELECT MateriaID, Nombre FROM Materias")
        
        filas = cursor.fetchall()
        conn.close()

        # Convertimos a JSON manual (para no usar zip si son pocas columnas)
        lista_materias = []
        for fila in filas:
            lista_materias.append({
                "id": fila.MateriaID, 
                "nombre": fila.Nombre
            })
            
        return jsonify(lista_materias)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTA 5: Obtener Lista de Carreras (Para el nuevo Dropdown) ---
@app.route('/carreras', methods=['GET'])
def listar_carreras():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT id_carrera, nombre_carrera FROM Carreras")
        filas = cursor.fetchall()
        conn.close()

        lista = [{"id": f.id_carrera, "nombre": f.nombre_carrera} for f in filas]
        return jsonify(lista)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTA 6: Registrar NUEVO Estudiante (INSERT) ---
@app.route('/estudiantes', methods=['POST'])
def registrar_estudiante():
    try:
        data = request.get_json()
        nombre = data['nombre']
        apellido = data['apellido']
        id_carrera = data['id_carrera']

        conn = obtener_conexion()
        cursor = conn.cursor()

        # Insertamos y pedimos el ID generado inmediatamente (SCOPE_IDENTITY)
        # CORRECCIÓN AQUÍ:
        # Agregamos "SET NOCOUNT ON;" al principio.
        # Esto evita que el mensaje de "1 row affected" confunda a Python.
        sql = """
            SET NOCOUNT ON;
            INSERT INTO Estudiantes (Nombre, Apellido, id_carrera)
            VALUES (?, ?, ?);
            SELECT SCOPE_IDENTITY();
        """
        cursor.execute(sql, (nombre, apellido, id_carrera))
        
        # Capturamos el ID del nuevo estudiante
        nuevo_id = cursor.fetchval() 
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success", 
            "mensaje": f"¡Bienvenido {nombre}! Tu matrícula es: {int(nuevo_id)}"
        })

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    
# --- RUTA 7: Ver Logs de Auditoría (ADMIN) ---
@app.route('/auditoria', methods=['GET'])
def ver_logs():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # TRUCO PRO: Formateamos la fecha directamente en SQL
        # 'dd/MM/yyyy HH:mm:ss' convierte "2026-01-28 14:00:00" en "28/01/2026 14:00:00"
        sql = """
            SELECT 
                e.Nombre + ' ' + e.Apellido AS Estudiante,
                a.NotaAnterior,
                a.NotaNueva,
                a.UsuarioResponsable AS Usuario,
                FORMAT(a.FechaCambio, 'dd/MM/yyyy HH:mm:ss') as Fecha
            FROM Auditoria_Calificaciones a
            INNER JOIN Estudiantes e ON a.EstudianteID = e.id_estudiante
            ORDER BY a.FechaCambio DESC
        """
        cursor.execute(sql)
        filas = cursor.fetchall()
        columnas = [column[0] for column in cursor.description]
        
        lista_logs = []
        for fila in filas:
            lista_logs.append(dict(zip(columnas, fila)))
            
        conn.close()
        return jsonify(lista_logs)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTA 8: Borrado Lógico (Soft Delete) ---
@app.route('/estudiantes/<int:id>', methods=['DELETE'])
def borrar_estudiante(id):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # EN LUGAR DE "DELETE FROM...", HACEMOS ESTO:
        sql = "UPDATE Estudiantes SET EstaActivo = 0 WHERE id_estudiante = ?"
        
        cursor.execute(sql, id)
        
        # Verificamos si alguien fue afectado
        if cursor.rowcount > 0:
            conn.commit()
            msg = "Estudiante desactivado correctamente. Su historial sigue guardado."
            status = "success"
        else:
            msg = "Estudiante no encontrado."
            status = "error"

        conn.close()
        return jsonify({"status": status, "mensaje": msg})

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# --- RUTA 9: EXPORTAR A EXCEL (REPORTING) ---
@app.route('/reporte/excel')
def descargar_excel():
    try:
        conn = obtener_conexion()
        
        # 1. Usamos Pandas para leer SQL directamente (¡Es una sola línea!)
        # Reutilizamos tu Vista para que el reporte salga bonito con nombres de carreras y todo
        sql = "SELECT * FROM vw_HistorialAcademico ORDER BY Apellido"
        df = pd.read_sql(sql, conn)
        
        conn.close()

        # 2. Creamos un archivo Excel en la Memoria RAM (Buffer)
        # Esto es mejor que guardarlo en el disco porque no llenas tu servidor de basura
        output = io.BytesIO()
        
        # Usamos un "Writer" para escribir en ese buffer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte General')
            
        # Volvemos el "puntero" al inicio del archivo para poder leerlo y enviarlo
        output.seek(0)

        # 3. Enviamos el archivo al navegador
        return send_file(
            output, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, 
            download_name='Reporte_Notas_UTESA.xlsx'
        )

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# --- RUTA 10: BUSCADOR EN VIVO (LIKE) ---
@app.route('/estudiantes/buscar', methods=['GET'])
def buscar_por_nombre():
    try:
        # 1. Capturamos lo que el usuario está escribiendo (?q=juan)
        query = request.args.get('q', '')
        
        # --- AGREGA ESTO ---
        print(f" BUSCANDO: '{query}'")
        # -------------------
        
        if not query:
            return jsonify([]) # Si no escribe nada, devolvemos lista vacía
        
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # 2. Usamos el operador LIKE con comodines %
        # Buscamos coincidencias en Nombre O en Apellido
        # En la función buscar_por_nombre:
        sql = """
            SELECT e.id_estudiante, e.Nombre, e.Apellido, 
                c.nombre_carrera  -- <--- AJUSTA AQUÍ SI ES NECESARIO
            FROM Estudiantes e
            JOIN Carreras c ON e.id_carrera = c.id_carrera
            WHERE (e.Nombre LIKE ? OR e.Apellido LIKE ?)
            AND e.EstaActivo = 1
        """
        # Le ponemos los % en Python antes de enviar a SQL
        parametro = f'%{query}%'
        cursor.execute(sql, (parametro,parametro))
        
        filas = cursor.fetchall()
        
        # --- AGREGA ESTO ---
        print(f" ENCONTRADOS: {len(filas)}")
        # -------------------
        conn.close()
        
        # 3. Formateamos la respuesta
        resultados = []
        for fila in filas:
            resultados.append({
                "id": fila.id_estudiante,
                "nombre_completo": f"{fila.Nombre} {fila.Apellido}",
                "carrera": fila.nombre_carrera
            })
        
        return jsonify(resultados)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- RUTA 11: DATOS PARA GRÁFICA (GROUP BY) ---
@app.route('/estadisticas/carreras', methods=['GET'])
def estadisticas_carreras():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # SQL AVANZADO: Contamos estudiantes agrupados por carrera
        # COUNT(*) cuenta cuántas filas hay en cada grupo
        sql = """
            SELECT c.nombre_carrera, COUNT(e.id_estudiante) as Total
            FROM Carreras c
            LEFT JOIN Estudiantes e ON c.id_carrera = e.id_carrera AND e.EstaActivo = 1
            GROUP BY c.nombre_carrera
        """
        
        cursor.execute(sql)
        filas = cursor.fetchall()
        conn.close
        
        # Preparamos dos listas separadas: Etiquetas (Nombres) y Valores (Números)
        # Esto es lo que pide Chart.js para dibujar
        labels = []
        data = []
        
        for fila in filas:
            labels.append(fila.nombre_carrera)
            data.append(fila.Total)
            
        return jsonify({
            "etiquetas" : labels,
            "valores": data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RUTA 12: INICIAR SESIÓN (LOGIN) ---
@app.route('/login', methods=['POST'])
def login():
    try:
        datos = request.get_json()
        usuario = datos.get('usuario')
        password = datos.get('password')

        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # Buscamos si existe ese usuario y contraseña
        sql = "SELECT NombreUsuario, Rol FROM Usuarios WHERE NombreUsuario = ? AND Password = ?"
        cursor.execute(sql, (usuario, password))
        user_db = cursor.fetchone()
        conn.close()

        if user_db:
            # ¡ÉXITO! Guardamos datos en la "Caja Fuerte" de la sesión
            session['usuario'] = user_db.NombreUsuario
            session['rol'] = user_db.Rol
            
            return jsonify({
                "status": "success", 
                "mensaje": f"Bienvenido, {user_db.NombreUsuario}",
                "rol": user_db.Rol
            })
        else:
            return jsonify({"status": "error", "mensaje": "Credenciales incorrectas"}), 401

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

# --- RUTA 13: CERRAR SESIÓN (LOGOUT) ---
@app.route('/logout')
def logout():
    session.clear() # Borramos todo rastro
    return jsonify({"status": "success", "mensaje": "Sesión cerrada"})

# --- ARRANCAR EL SERVIDOR ---
if __name__ == '__main__':
    print(" Servidor corriendo en http://127.0.0.1:5000")
    app.run(debug=True)
