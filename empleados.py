"""Módulo de EMPLEADOS (Paso 4): insertar y consultas generales."""
import tkinter as tk
from tkinter import messagebox
from conexion import obtener_conexion
from tabla import mostrar_tabla
from esquema import columna_pk
import sesion

TABLA_EMPLEADAS = "empleado"


def consultas_generales(padre):
    mostrar_tabla(padre, "Consultas generales - Empleadas", TABLA_EMPLEADAS)


def _columnas_tabla(tabla):
    conexion = obtener_conexion()
    with conexion.cursor() as cur:
        cur.execute(
            """SELECT column_name
               FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = %s
               ORDER BY ordinal_position""",
            (tabla,),
        )
        return [fila[0] for fila in cur.fetchall()]


def insertar_empleado(padre):
    conexion = obtener_conexion()
    try:
        columnas = _columnas_tabla(TABLA_EMPLEADAS)
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", f"No pude leer la estructura de {TABLA_EMPLEADAS}:\n{error}")
        return

    if not columnas:
        messagebox.showerror("Error", f"No se encontró la tabla '{TABLA_EMPLEADAS}' en la base de datos.")
        return

    pk = columna_pk(TABLA_EMPLEADAS) or columnas[0]

    win = tk.Toplevel(padre)
    win.title(f"Insertar empleado - Usuario: {sesion.obtener()}")
    win.geometry(f"340x{140 + len(columnas) * 52}")
    sesion.poner_saludo(win)

    entradas = {}
    for col in columnas:
        etiqueta = f"{col} (vacío = automático)" if col == pk else col
        tk.Label(win, text=f"{etiqueta}:").pack(pady=(8, 0))
        es_pass = "contra" in col.lower() or "pass" in col.lower()
        e = tk.Entry(win, width=32, show="*" if es_pass else "")
        e.pack()
        entradas[col] = e

    def guardar():
        valores_raw = {col: entradas[col].get().strip() for col in columnas}

        # Validar obligatorios (nombre y contraseña)
        for col, val in valores_raw.items():
            if col != pk and ("nombre" in col.lower() or "contra" in col.lower()) and not val:
                messagebox.showwarning("Faltan datos", f"El campo '{col}' es obligatorio.")
                return

        if valores_raw.get(pk) and not valores_raw[pk].isdigit():
            messagebox.showwarning("ID inválido", f"El campo '{pk}' debe ser un número.")
            return

        cols_insert = []
        vals_insert = []
        for col in columnas:
            val = valores_raw[col]
            if col == pk:
                if val:
                    cols_insert.append(col)
                    vals_insert.append(int(val))
            else:
                cols_insert.append(col)
                vals_insert.append(val if val != "" else None)

        placeholders = ", ".join(["%s"] * len(cols_insert))
        cols_sql = ", ".join(cols_insert)

        try:
            with conexion.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {TABLA_EMPLEADAS} ({cols_sql}) VALUES ({placeholders})",
                    vals_insert,
                )
                if pk in cols_insert:
                    cur.execute(
                        f"""SELECT setval(pg_get_serial_sequence('{TABLA_EMPLEADAS}', '{pk}'),
                                         (SELECT MAX({pk}) FROM {TABLA_EMPLEADAS}))"""
                    )
            conexion.commit()
            messagebox.showinfo("Listo", "Empleado insertado correctamente.")
            for e in entradas.values():
                e.delete(0, tk.END)
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al insertar", str(error))

    tk.Button(win, text="Guardar", width=14, command=guardar).pack(pady=16)