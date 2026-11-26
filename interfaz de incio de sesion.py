"""ARCHIVO PRINCIPAL: ejecuta este para iniciar el programa (login)."""
import tkinter as tk
from tkinter import messagebox
from conexion import conectar, guardar_conexion, cerrar_conexion
import sesion
from autenticacion import (ADMIN_USUARIO, ADMIN_CONTRASENA,
                           validar_empleado, validar_doctor)
from menu_principal import abrir_ventana_principal


def entrar():
    usuario = entry_usuario.get().strip()
    contrasena = entry_contrasena.get()

    if not usuario or not contrasena:
        messagebox.showwarning("Campos vacíos", "Por favor ingresa usuario y contraseña.")
        return

    conexion = conectar(usuario, contrasena)
    if not conexion:
        return
    guardar_conexion(conexion)

    # 1) ¿Es el administrador?
    if usuario == ADMIN_USUARIO and contrasena == ADMIN_CONTRASENA:
        nombre, rol, id_usr = "ADMINISTRADOR", "admin", None
    else:
        # 2) ¿Es una empleada registrada? (usuario = código)
        try:
            nombre_emp = validar_empleado(usuario, contrasena)
        except Exception as error:
            messagebox.showerror("Error al validar", str(error))
            cerrar_conexion()
            return

        if nombre_emp:
            nombre, rol, id_usr = nombre_emp, "empleado", usuario
        else:
            # 3) ¿Es un doctor registrado? (usuario = ID del doctor)
            try:
                doc = validar_doctor(usuario, contrasena)
            except Exception as error:
                messagebox.showerror("Error al validar", str(error))
                cerrar_conexion()
                return

            if doc:
                id_usr, nombre = doc
                rol = "doctor"
            else:
                messagebox.showerror("Acceso denegado", "Código o contraseña incorrectos.")
                cerrar_conexion()
                return

    sesion.iniciar(nombre, id_usr)              # recuerda quién entró y su ID
    ventana.withdraw()                          # oculta el login
    abrir_ventana_principal(ventana, nombre, rol, volver_al_login)


def volver_al_login():
    """Se llama al cerrar sesión: limpia los campos y muestra el login otra vez."""
    entry_usuario.delete(0, tk.END)
    entry_contrasena.delete(0, tk.END)
    ventana.deiconify()
    entry_usuario.focus()


def salir():
    ventana.destroy()


# ==========================================
# INTERFAZ GRÁFICA (Tkinter) - LOGIN
# ==========================================
ventana = tk.Tk()
ventana.title("Inicio de Sesión")
ventana.geometry("340x300")
ventana.resizable(False, False)

tk.Label(ventana, text="Usuario:").pack(pady=(30, 5))
entry_usuario = tk.Entry(ventana)
entry_usuario.pack()

tk.Label(ventana, text="Contraseña:").pack(pady=(15, 5))
entry_contrasena = tk.Entry(ventana, show="*")
entry_contrasena.pack()

frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=25)

tk.Button(frame_botones, text="Entrar", width=10, command=entrar).pack(side=tk.LEFT, padx=10)
tk.Button(frame_botones, text="Salir", width=10, command=salir).pack(side=tk.LEFT, padx=10)

ventana.mainloop()