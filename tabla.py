"""Funciones reutilizables para mostrar tablas y consultas de la BD en una ventana."""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import obtener_conexion
import sesion


def _formatear(valor):
    if valor is None:
        return ""
    if isinstance(valor, datetime.time):
        return valor.strftime("%H:%M")
    return valor


def mostrar_consulta(padre, titulo, consulta, params=()):
    """Ejecuta un SELECT y muestra el resultado en una tabla."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cur:
            cur.execute(consulta, params)
            columnas = [c.name for c in cur.description]
            filas = cur.fetchall()
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", str(error))
        return

    win = tk.Toplevel(padre)
    win.title(f"{titulo} - Usuario: {sesion.obtener()}")
    win.geometry("800x380")
    sesion.poner_saludo(win)

    tabla = ttk.Treeview(win, columns=columnas, show="headings")
    for col in columnas:
        tabla.heading(col, text=col.upper())
        tabla.column(col, width=110, anchor="center")
    for fila in filas:
        tabla.insert("", tk.END, values=[_formatear(v) for v in fila])

    scroll = ttk.Scrollbar(win, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tabla.pack(fill=tk.BOTH, expand=True)


def mostrar_tabla(padre, titulo, tabla_bd, orden=None):
    consulta = f"SELECT * FROM {tabla_bd}"
    if orden:
        consulta += f" ORDER BY {orden}"
    mostrar_consulta(padre, titulo, consulta)