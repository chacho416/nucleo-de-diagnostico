"""Módulo de DOCTORES (Pasos 6 y 8)."""
import tkinter as tk
from tkinter import messagebox
from conexion import obtener_conexion
from tabla import mostrar_tabla
from esquema import columna_pk
import sesion


def consultas_generales(padre):
    mostrar_tabla(padre, "Consultas generales - Doctores", "doctor", orden="1")


def insertar_doctor(padre):
    win = tk.Toplevel(padre)
    win.title(f"Insertar doctor - Usuario: {sesion.obtener()}")
    win.geometry("320x525")
    sesion.poner_saludo(win)

    campos = ["ID doctor (vacío = automático)", "Nombre", "Dirección", "Teléfono",
              "Fecha nacimiento (AAAA-MM-DD)", "Sexo (M/F)",
              "Especialidad", "Contraseña"]
    entradas = {}
    for campo in campos:
        tk.Label(win, text=campo + ":").pack(pady=(8, 0))
        e = tk.Entry(win, width=30, show="*" if campo == "Contraseña" else "")
        e.pack()
        entradas[campo] = e

    def guardar():
        conexion = obtener_conexion()
        pk = columna_pk("doctor") or "id"   # nombre real de la llave primaria
        v = [entradas[c].get().strip() for c in campos]
        # v = [id, nombre, direccion, telefono, fecha_nac, sexo, especialidad, contrasena]
        if not v[1] or not v[7]:
            messagebox.showwarning("Faltan datos", "Nombre y contraseña son obligatorios.")
            return
        if v[0] and not v[0].isdigit():
            messagebox.showwarning("ID inválido", "El ID del doctor debe ser un número.")
            return
        try:
            with conexion.cursor() as cur:
                if v[0]:
                    cur.execute(
                        f"""INSERT INTO doctor
                           ({pk}, nombre, direccion, telefono, fecha_nac, sexo, especialidad, contrasena)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (int(v[0]), v[1], v[2], v[3], v[4] or None,
                         v[5].upper() or None, v[6], v[7]),
                    )
                    cur.execute(
                        f"""SELECT setval(pg_get_serial_sequence('doctor', '{pk}'),
                                         (SELECT MAX({pk}) FROM doctor))"""
                    )
                else:
                    cur.execute(
                        """INSERT INTO doctor
                           (nombre, direccion, telefono, fecha_nac, sexo, especialidad, contrasena)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (v[1], v[2], v[3], v[4] or None, v[5].upper() or None, v[6], v[7]),
                    )
            conexion.commit()
            messagebox.showinfo("Listo", f"Doctor {v[1]} insertado correctamente.")
            for e in entradas.values():
                e.delete(0, tk.END)
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al insertar", str(error))

    tk.Button(win, text="Guardar", width=12, command=guardar).pack(pady=15)