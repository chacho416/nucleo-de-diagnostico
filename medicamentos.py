"""Módulo de MEDICAMENTOS: insertar (dar de alta) y consultas generales."""
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import obtener_conexion
from tabla import mostrar_tabla
from esquema import columna_pk
from calendario import SelectorFecha
import sesion

PRESENTACIONES = [
    "Tabletas", "Cápsulas", "Jarabe", "Suspensión", "Solución inyectable",
    "Crema", "Pomada", "Gotas", "Supositorios", "Aerosol", "Otro"
]

VIAS_ADMINISTRACION = [
    "Oral", "Intravenosa", "Intramuscular", "Subcutánea", "Tópica",
    "Oftálmica", "Ótica", "Nasal", "Rectal", "Inhalatoria", "Sublingual"
]


def consultas_generales(padre):
    mostrar_tabla(padre, "Consultas generales - Medicamentos", "medicamento", orden="1")


def insertar_medicamento(padre):
    win = tk.Toplevel(padre)
    win.title(f"Insertar medicamento - Usuario: {sesion.obtener()}")
    win.geometry("360x450")
    sesion.poner_saludo(win)

    tk.Label(win, text="ID medicamento (vacío = automático):").pack(pady=(8, 0))
    entry_id = tk.Entry(win, width=32)
    entry_id.pack()

    tk.Label(win, text="Nombre:").pack(pady=(8, 0))
    entry_nombre = tk.Entry(win, width=32)
    entry_nombre.pack()

    tk.Label(win, text="Presentación:").pack(pady=(8, 0))
    cb_presentacion = ttk.Combobox(win, values=PRESENTACIONES, width=29)
    cb_presentacion.pack()

    tk.Label(win, text="Vía de administración:").pack(pady=(8, 0))
    cb_via = ttk.Combobox(win, values=VIAS_ADMINISTRACION, width=29)
    cb_via.pack()

    tk.Label(win, text="Caducidad:").pack(pady=(8, 0))
    sel_caducidad = SelectorFecha(win)
    sel_caducidad.pack(pady=(2, 0))

    def guardar():
        conexion = obtener_conexion()
        pk = columna_pk("medicamento") or "id_medicamento"

        id_med = entry_id.get().strip()
        nombre = entry_nombre.get().strip()
        presentacion = cb_presentacion.get().strip()
        via = cb_via.get().strip()
        caducidad = sel_caducidad.get()

        if not nombre or not presentacion or not via or not caducidad:
            messagebox.showwarning(
                "Faltan datos",
                "Nombre, presentación, vía de administración y caducidad son obligatorios."
            )
            return
        if id_med and not id_med.isdigit():
            messagebox.showwarning("ID inválido", "El ID del medicamento debe ser un número.")
            return

        try:
            with conexion.cursor() as cur:
                if id_med:
                    cur.execute(
                        f"""INSERT INTO medicamento
                           ({pk}, nombre, presentacion, via_administracion, caducidad)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (int(id_med), nombre, presentacion, via, caducidad),
                    )
                    cur.execute(
                        f"""SELECT setval(pg_get_serial_sequence('medicamento', '{pk}'),
                                         (SELECT MAX({pk}) FROM medicamento))"""
                    )
                else:
                    cur.execute(
                        """INSERT INTO medicamento
                           (nombre, presentacion, via_administracion, caducidad)
                           VALUES (%s, %s, %s, %s)""",
                        (nombre, presentacion, via, caducidad),
                    )
            conexion.commit()
            messagebox.showinfo("Listo", f"Medicamento '{nombre}' insertado correctamente.")
            entry_id.delete(0, tk.END)
            entry_nombre.delete(0, tk.END)
            cb_presentacion.set("")
            cb_via.set("")
            sel_caducidad.clear()
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al insertar", str(error))

    tk.Button(win, text="Guardar", width=14, command=guardar).pack(pady=18)