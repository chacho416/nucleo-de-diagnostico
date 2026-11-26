"""Validación de usuarios: administrador, empleadas y doctores (login por código y contraseña)."""
from conexion import obtener_conexion
from esquema import columna_pk

# --- Administrador
ADMIN_USUARIO = "admin"
ADMIN_CONTRASENA = "1234"

# --- Nombres de empleado (login)
TABLA_EMPLEADO = "empleado"
COL_ID = "ID"
COL_NOMBRE = "nombre"
COL_CONTRASENA = "contrasena"


def validar_empleado(id, contrasena):
    """Devuelve el nombre de la empleada si el código y la contraseña son correctos; si no, None."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cur:
            cur.execute(
                f"SELECT {COL_NOMBRE} FROM {TABLA_EMPLEADO} "
                f"WHERE {COL_ID}::text = %s AND {COL_CONTRASENA} = %s",
                (id, contrasena),
            )
            fila = cur.fetchone()
        return fila[0] if fila else None
    except Exception:
        conexion.rollback()
        raise


def validar_doctor(id_doctor, contrasena):
    """Devuelve (id_doctor, nombre) si el ID y la contraseña del doctor son correctos; si no, None."""
    conexion = obtener_conexion()
    pk = columna_pk("doctor") or "id_doctor"
    try:
        with conexion.cursor() as cur:
            cur.execute(
                f"SELECT {pk}, nombre FROM doctor "
                f"WHERE {pk}::text = %s AND contrasena = %s",
                (id_doctor, contrasena),
            )
            fila = cur.fetchone()
        return (fila[0], fila[1]) if fila else None
    except Exception:
        conexion.rollback()
        raise