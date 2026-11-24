import sqlite3
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

DB_NAME = "asistencia_institucion.db"

def conectar():
    return sqlite3.connect(DB_NAME)

def inicializar_bd():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('ALUMNO', 'PROFESOR')) NOT NULL,
            año INTEGER CHECK(año BETWEEN 1 AND 6) NOT NULL,
            seccion TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            estado TEXT CHECK(estado IN ('PRESENTE', 'AUSENTE', 'JUSTIFICADO')) NOT NULL,
            horas TEXT DEFAULT '1h',
            materia TEXT DEFAULT 'General',
            observacion TEXT,
            FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS docentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre_apellido TEXT NOT NULL,
            materia TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS control_horas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            docente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            horas INTEGER NOT NULL,
            FOREIGN KEY (docente_id) REFERENCES docentes(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credenciales (
            año INTEGER PRIMARY KEY,
            rol TEXT NOT NULL,
            clave TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL,
            accion TEXT NOT NULL,
            fecha_hora TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM credenciales")
    if cursor.fetchone()[0] == 0:
        default_users = [
            (0, "Administrador General", "admin123"),
            (1, "Coordinación de 1er Año", "coord1"),
            (2, "Coordinación de 2do Año", "coord2"),
            (3, "Coordinación de 3er Año", "coord3"),
            (4, "Coordinación de 4to Año", "coord4"),
            (5, "Coordinación de 5to Año", "coord5"),
            (6, "Coordinación de 6to Año", "coord6"),
        ]
        cursor.executemany("INSERT INTO credenciales (año, rol, clave) VALUES (?, ?, ?)", default_users)
        conexion.commit()
    
    conexion.commit()
    conexion.close()

def registrar_auditoria(rol, accion):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO auditoria (rol, accion, fecha_hora) VALUES (?, ?, ?)", (rol, accion, ahora))
        conexion.commit()
        conexion.close()
    except Exception:
        pass

def obtener_logs_auditoria():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, rol, accion, fecha_hora FROM auditoria ORDER BY id DESC LIMIT 100")
    logs = cursor.fetchall()
    conexion.close()
    return logs

def verificar_login(año, clave):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT clave, rol FROM credenciales WHERE año = ?", (año,))
    resultado = cursor.fetchone()
    conexion.close()
    
    rol_nombre = "Administrador General" if año == 0 else f"Coordinación de {año}° Año"
    
    if resultado and resultado[0] == clave:
        registrar_auditoria(rol_nombre, f"Inicio de sesión exitoso en el departamento {rol_nombre}.")
        return True
    else:
        registrar_auditoria("Sistema / Seguridad", f"⚠️ INTENTO FALLIDO: Credenciales incorrectas para '{rol_nombre}'.")
        return False

def obtener_persona_por_id(persona_id):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, cedula, nombre, apellido, tipo, año, seccion FROM personas WHERE id = ?", (persona_id,))
        p = cursor.fetchone()
        conexion.close()
        return p
    except Exception:
        return None

def registrar_persona(cedula, nombre, apellido, tipo, año, seccion, rol_usuario="Sistema"):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO personas (cedula, nombre, apellido, tipo, año, seccion) VALUES (?, ?, ?, ?, ?, ?)",
            (cedula, nombre, apellido, tipo.upper(), año, seccion.upper())
        )
        conexion.commit()
        conexion.close()
        registrar_auditoria(rol_usuario, f"Registró a {tipo.upper()} {nombre} {apellido} (Cédula: {cedula})")
        return True
    except sqlite3.IntegrityError:
        return False

def modificar_persona(persona_id, nombre, apellido, tipo, año, seccion, rol_usuario="Sistema"):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE personas SET nombre = ?, apellido = ?, tipo = ?, año = ?, seccion = ? WHERE id = ?",
            (nombre, apellido, tipo.upper(), año, seccion.upper(), persona_id)
        )
        conexion.commit()
        filas = cursor.rowcount
        conexion.close()
        if filas > 0:
            registrar_auditoria(rol_usuario, f"Modificó los datos del miembro ID {persona_id} ({nombre} {apellido})")
            return True
        return False
    except Exception:
        return False

def eliminar_persona(persona_id, rol_usuario="Sistema"):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
    conexion.commit()
    filas = cursor.rowcount
    conexion.close()
    if filas > 0:
        registrar_auditoria(rol_usuario, f"Eliminó al miembro ID {persona_id}")
        return True
    return False

def obtener_personas_por_coordinacion(año):
    conexion = conectar()
    cursor = conexion.cursor()
    if año == 0:
        cursor.execute("SELECT id, cedula, nombre, apellido, tipo, año, seccion FROM personas")
    else:
        cursor.execute("SELECT id, cedula, nombre, apellido, tipo, año, seccion FROM personas WHERE año = ?", (año,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def obtener_alumnos_por_seccion(año, seccion):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, cedula, nombre, apellido, año, seccion FROM personas WHERE tipo = 'ALUMNO' AND año = ? AND seccion = ? ORDER BY apellido", (año, seccion))
    res = cursor.fetchall()
    conexion.close()
    return res

def obtener_secciones_disponibles(año):
    conexion = conectar()
    cursor = conexion.cursor()
    if año == 0:
        cursor.execute("SELECT DISTINCT seccion FROM personas ORDER BY seccion")
    else:
        cursor.execute("SELECT DISTINCT seccion FROM personas WHERE año = ? ORDER BY seccion", (año,))
    secs = [row[0] for row in cursor.fetchall()]
    conexion.close()
    return secs

def obtener_estadisticas(año):
    conexion = conectar()
    cursor = conexion.cursor()
    if año == 0:
        cursor.execute("SELECT COUNT(*) FROM personas WHERE tipo='ALUMNO'")
        total_alumnos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM personas WHERE tipo='PROFESOR'")
        total_profesores = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM asistencia")
        total_asistencias = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM personas WHERE tipo='ALUMNO' AND año=?", (año,))
        total_alumnos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM personas WHERE tipo='PROFESOR' AND año=?", (año,))
        total_profesores = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM asistencia a JOIN personas p ON a.persona_id = p.id WHERE p.año=?", (año,))
        total_asistencias = cursor.fetchone()[0]
    conexion.close()
    return total_alumnos, total_profesores, total_asistencias

def obtener_inasistencias(año):
    conexion = conectar()
    cursor = conexion.cursor()
    if año == 0:
        cursor.execute("""
            SELECT a.id, p.cedula, p.nombre, p.apellido, p.tipo, p.año, p.seccion, a.fecha, a.estado, a.materia, a.observacion
            FROM asistencia a
            JOIN personas p ON a.persona_id = p.id
            WHERE a.estado = 'AUSENTE'
            ORDER BY a.fecha DESC
        """)
    else:
        cursor.execute("""
            SELECT a.id, p.cedula, p.nombre, p.apellido, p.tipo, p.año, p.seccion, a.fecha, a.estado, a.materia, a.observacion
            FROM asistencia a
            JOIN personas p ON a.persona_id = p.id
            WHERE a.estado = 'AUSENTE' AND p.año = ?
            ORDER BY a.fecha DESC
        """, (año,))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def registrar_asistencia_avanzada(persona_id, fecha, estado, horas, materia, observacion, rol_usuario="Sistema"):
    persona = obtener_persona_por_id(persona_id)
    if not persona:
        return False, "El ID ingresado no está registrado."
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO asistencia (persona_id, fecha, estado, horas, materia, observacion) VALUES (?, ?, ?, ?, ?, ?)",
            (persona_id, fecha, estado.upper(), horas, materia, observacion)
        )
        conexion.commit()
        conexion.close()
        registrar_auditoria(rol_usuario, f"Registró asistencia [{estado}] para {persona[2]} {persona[3]} (Materia: {materia})")
        return True, "Asistencia registrada con éxito."
    except Exception as e:
        return False, f"Error: {e}"

def gestionar_docente(cedula, nombre_apellido, materia, rol_usuario="Sistema"):
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO docentes (cedula, nombre_apellido, materia) VALUES (?, ?, ?)", (cedula, nombre_apellido, materia))
        conexion.commit()
        conexion.close()
        registrar_auditoria(rol_usuario, f"Registró docente: {nombre_apellido}")
        return True, "Docente registrado con éxito."
    except Exception as e:
        return False, f"Error: {e}"

def obtener_docentes():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, cedula, nombre_apellido, materia FROM docentes")
    docs = cursor.fetchall()
    conexion.close()
    return docs

def eliminar_docente(doc_id, rol_usuario="Sistema"):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM docentes WHERE id = ?", (doc_id,))
    conexion.commit()
    conexion.close()
    registrar_auditoria(rol_usuario, f"Eliminó al docente ID {doc_id}")
    return True

def promover_alumnos_institucion(rol_usuario="Sistema"):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM personas WHERE tipo = 'ALUMNO' AND año = 6")
    for i in range(5, 0, -1):
        cursor.execute("UPDATE personas SET año = ? WHERE tipo = 'ALUMNO' AND año = ?", (i + 1, i))
    conexion.commit()
    conexion.close()
    registrar_auditoria(rol_usuario, "Ejecutó la promoción general de alumnos al siguiente año escolar.")

def importar_archivo_masivo(ruta_archivo, rol_usuario="Sistema"):
    try:
        ext = ruta_archivo.lower().split('.')[-1]
        if ext == 'csv':
            df = pd.read_csv(ruta_archivo)
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(ruta_archivo)
        else:
            return False, "Formato no soportado. Use .csv o .xlsx"
        
        exitosos = 0
        for _, row in df.iterrows():
            if registrar_persona(
                str(row['cedula']), str(row['nombre']), str(row['apellido']),
                str(row['tipo']), int(row['año']), str(row['seccion']), rol_usuario
            ):
                exitosos += 1
        registrar_auditoria(rol_usuario, f"Importó {exitosos} registros desde archivo {ext.upper()}")
        return True, f"Se importaron {exitosos} registros con éxito."
    except Exception as e:
        return False, f"Error al procesar archivo: {e}"

def exportar_a_archivo(ruta_salida, año_filtro=0, formato="xlsx", rol_usuario="Sistema"):
    try:
        datos = obtener_personas_por_coordinacion(año_filtro)
        df = pd.DataFrame(datos, columns=['ID', 'Cédula', 'Nombre', 'Apellido', 'Tipo', 'Año', 'Sección'])
        if formato.lower() == 'csv':
            df.to_csv(ruta_salida, index=False, encoding='utf-8')
        else:
            df.to_excel(ruta_salida, index=False)
        registrar_auditoria(rol_usuario, f"Exportó el directorio a formato {formato.upper()}")
        return True, f"Exportado correctamente como .{formato}."
    except Exception as e:
        return False, f"Error al exportar: {e}"

def generar_constancia_pdf(persona_id, ruta_salida):
    p = obtener_persona_por_id(persona_id)
    if not p:
        return False, "Persona no encontrada."
    try:
        c = canvas.Canvas(ruta_salida, pagesize=letter)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(150, 750, "REPÚBLICA BOLIVARIANA DE VENEZUELA")
        c.setFont("Helvetica", 12)
        c.drawString(210, 725, "SISTEMA EDUCATIVO INSTITUCIONAL")
        c.line(50, 710, 560, 710)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(305, 650, "CONSTANCIA OFICIAL DE REGISTRO")
        c.setFont("Helvetica", 12)
        texto = f"""
        Se hace constar por medio de la presente que el ciudadano(a):
        
        Nombres y Apellidos: {p[2]} {p[3]}
        Cédula de Identidad: V-{p[1]}
        Rol / Tipo: {p[4]}
        Año Académico: {p[5]}° Año | Sección: {p[6]}
        
        Expedido en Charallave, a los {datetime.now().strftime('%d días del mes de %Y')}.
        """
        y = 580
        for linea in texto.strip().split('\n'):
            c.drawString(70, y, linea.strip())
            y -= 25
        c.drawString(100, 300, "___________________________________")
        c.drawString(120, 280, "Firma y Sello Autorizado")
        c.save()
        return True, "PDF generado con éxito."
    except Exception as e:
        return False, f"Error PDF: {e}"