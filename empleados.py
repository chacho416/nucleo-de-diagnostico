"""Módulo de EMPLEADOS (Paso 4)."""
import tkinter as tk
from tkinter import messagebox
from psycopg import sql
from conexion import obtener_conexion
from tabla import mostrar_tabla
import sesion

TABLA_EMPLEADAS = "empleado"


def consultas_generales(padre):
    mostrar_tabla(padre, "Consultas generales - Empleadas", TABLA_EMPLEADAS)


def insertar_empleado(padre):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cur:
            cur.execute(
                """SELECT column_name, is_nullable, column_default, data_type
                   FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = %s
                   ORDER BY ordinal_position""",
                (TABLA_EMPLEADAS,),
            )
            columnas = cur.fetchall()
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", str(error))
        return

    if not columnas:
        messagebox.showerror("Error", f"No existe la tabla '{TABLA_EMPLEADAS}'.")
        return

    win = tk.Toplevel(padre)
    win.title(f"Insertar empleado - Usuario: {sesion.obtener()}")
    win.geometry(f"340x{120 + 52 * len(columnas)}")
    sesion.poner_saludo(win)

    entradas = {}
    for nombre, nullable, default, tipo in columnas:
        etiqueta = nombre.replace("_", " ").capitalize()
        if default is not None:
            etiqueta += " (vacío = automático)"
        elif tipo == "date":
            etiqueta += " (AAAA-MM-DD)"
        tk.Label(win, text=etiqueta + ":").pack(pady=(4, 0))
        e = tk.Entry(
            win,
            width=32,
            show="*" if "contras" in nombre.lower() else "",
        )
        e.pack()
        entradas[nombre] = e

    def guardar():
        cols, vals = [], []
        for nombre, nullable, default, tipo in columnas:
            valor = entradas[nombre].get().strip()
            if valor == "":
                if default is None and nullable == "NO":
                    messagebox.showwarning(
                        "Faltan datos",
                        f"El campo '{nombre}' es obligatorio.",
                    )
                    return
                continue
            cols.append(nombre)
            vals.append(valor)

        if not cols:
            messagebox.showwarning("Faltan datos", "Llena el formulario del empleado.")
            return

        consulta = sql.SQL("INSERT INTO {t} ({c}) VALUES ({v})").format(
            t=sql.Identifier(TABLA_EMPLEADAS),
            c=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
            v=sql.SQL(", ").join(sql.Placeholder() * len(cols)),
        )
        try:
            with conexion.cursor() as cur:
                cur.execute(consulta, vals)
                for nombre, nullable, default, tipo in columnas:
                    if nombre in cols and default and "nextval" in default:
                        cur.execute(
                            sql.SQL(
                                "SELECT setval(pg_get_serial_sequence({t}, {c}), "
                                "(SELECT MAX({i}) FROM {tt}))"
                            ).format(
                                t=sql.Literal(TABLA_EMPLEADAS),
                                c=sql.Literal(nombre),
                                i=sql.Identifier(nombre),
                                tt=sql.Identifier(TABLA_EMPLEADAS),
                            )
                        )
            conexion.commit()
            messagebox.showinfo("Listo", "Empleado registrado correctamente.")
            for entrada in entradas.values():
                entrada.delete(0, tk.END)
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al insertar", str(error))

    tk.Button(win, text="Guardar", width=12, command=guardar).pack(pady=15)