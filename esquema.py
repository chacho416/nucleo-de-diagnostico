"""Utilidades para leer la estructura de la base de datos."""
from conexion import obtener_conexion


def columna_pk(tabla):
    """Devuelve el nombre de la columna llave primaria de una tabla (ej. 'id_paciente' o 'id').
    Devuelve None si no la encuentra."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """SELECT kcu.column_name
                   FROM information_schema.table_constraints tc
                   JOIN information_schema.key_column_usage kcu
                     ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                   WHERE tc.constraint_type = 'PRIMARY KEY'
                     AND tc.table_schema = 'public'
                     AND tc.table_name = %s
                   ORDER BY kcu.ordinal_position""",
                (tabla,),
            )
            fila = cur.fetchone()
        return fila[0] if fila else None
    except Exception:
        conexion.rollback()
        return None