"""Ventana principal con la barra de menús y el saludo del usuario."""
import tkinter as tk
from tkinter import messagebox
from conexion import cerrar_conexion
import sesion
import empleados
import doctores
import paciente
import cita


def crear_imagen_diagnostico():
    ancho, alto = 240, 150
    img = tk.PhotoImage(width=ancho, height=alto)
    img.put("#e8f1f8", to=(0, 0, ancho, alto))
    img.put("#1f4e78", to=(0, 0, ancho, 4))
    img.put("#1f4e78", to=(0, alto - 4, ancho, alto))
    img.put("#1f4e78", to=(0, 0, 4, alto))
    img.put("#1f4e78", to=(ancho - 4, 0, ancho, alto))
    img.put("#1f4e78", to=(105, 32, 135, 118))
    img.put("#1f4e78", to=(77, 60, 163, 90))
    return img


def abrir_menu_principal(raiz, nombre, rol, volver_al_login):
    principal = tk.Toplevel(raiz)
    principal.title("Sistema - Núcleo de Diagnóstico")
    principal.geometry("560x430")

    def cerrar_todo():
        cerrar_conexion()
        raiz.destroy()

    def cerrar_sesion():
        if not messagebox.askyesno("Cerrar sesión",
                                   "¿Seguro que quieres cerrar sesión?", parent=principal):
            return                   # eligió "No": no pasa nada
        cerrar_conexion()
        sesion.cerrar()
        principal.destroy()      # cierra el sistema (y sus ventanas hijas)
        volver_al_login()        # vuelve a mostrar el login

    principal.protocol("WM_DELETE_WINDOW", cerrar_todo)

    barra = tk.Menu(principal)

    # El administrador ve Empleados y Doctores
    if rol == "admin":
        menu_emp = tk.Menu(barra, tearoff=0)
        menu_emp.add_command(label="Consultas generales",
                             command=lambda: empleados.consultas_generales(principal))
        barra.add_cascade(label="Empleados", menu=menu_emp)

        menu_doc = tk.Menu(barra, tearoff=0)
        menu_doc.add_command(label="Insertar doctor",
                             command=lambda: doctores.insertar_doctor(principal))
        menu_doc.add_command(label="Consultas generales",
                             command=lambda: doctores.consultas_generales(principal))
        barra.add_cascade(label="Doctores", menu=menu_doc)

    # Todos (administrador y empleadas) ven Pacientes
    menu_pac = tk.Menu(barra, tearoff=0)
    menu_pac.add_command(label="Insertar",
                         command=lambda: paciente.insertar_paciente(principal))
    menu_pac.add_command(label="Consultas generales",
                         command=lambda: paciente.consultas_generales(principal))
    barra.add_cascade(label="Pacientes", menu=menu_pac)

    # Citas: administrador y empleadas
    menu_cita = tk.Menu(barra, tearoff=0)
    menu_cita.add_command(label="Registrar cita",
                          command=lambda: cita.registrar_cita(principal))
    menu_cita.add_command(label="Modificar cita",
                          command=lambda: cita.modificar_cita(principal))
    menu_cita.add_command(label="Consultas generales",
                          command=lambda: cita.consultas_generales(principal))
    barra.add_cascade(label="Citas", menu=menu_cita)

    barra.add_command(label="Cerrar sesión", command=cerrar_sesion)
    principal.config(menu=barra)

    # Saludo en la parte superior derecha
    sesion.poner_saludo(principal)

    # Título e imagen centrados
    contenedor = tk.Frame(principal)
    contenedor.pack(expand=True)

    tk.Label(
        contenedor,
        text="SISTEMA DE GESTIÓN\nNÚCLEO DE DIAGNÓSTICO",
        font=("Arial", 15, "bold"),
        fg="#1f4e78"
    ).pack(pady=15)

    principal.imagen_diagnostico = crear_imagen_diagnostico()   # guarda la referencia
    tk.Label(contenedor, image=principal.imagen_diagnostico).pack(pady=10)
