"""ARCHIVO PRINCIPAL: ejecuta este para iniciar el programa (login)."""
import tkinter as tk
from tkinter import messagebox
import conexion
import sesion
import autenticacion
import menu_principal


def entrar():
    usuario = entry_usuario.get().strip()
    contrasena = entry_contrasena.get()

    if not usuario or not contrasena:
        messagebox.showwarning("Campos vacíos", "Por favor ingresa usuario y contraseña.")
        return

    conexion_db = conexion.conectar(usuario, contrasena)
    if not conexion_db:
        return
    conexion.guardar_conexion(conexion_db)

    # 1) ¿Es el administrador?
    if (usuario == autenticacion.ADMIN_USUARIO
            and contrasena == autenticacion.ADMIN_CONTRASENA):
        nombre, rol = "ADMINISTRADOR", "admin"
    else:
        # 2) ¿Es una empleada registrada? (usuario = código)
        try:
            nombre = autenticacion.validar_empleado(usuario, contrasena)
        except Exception as error:
            messagebox.showerror("Error al validar", str(error))
            conexion.cerrar_conexion()
            return
        rol = "empleado"
        if not nombre:
            messagebox.showerror("Acceso denegado", "Código o contraseña incorrectos.")
            conexion.cerrar_conexion()
            return

    sesion.iniciar(nombre)                       # recuerda quién entró
    ventana.withdraw()                           # oculta el login
    menu_principal.abrir_ventana_principal(
        ventana, nombre, rol, volver_al_login
    )  # "Hola, NOMBRE"


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
ventana.geometry("340x470")
ventana.resizable(False, False)


tk.Label(ventana, text="Usuario:").pack(pady=(15, 5))
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
