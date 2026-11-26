import tkinter as tk
from tkinter import messagebox
from conexion import cerrar_conexion
import sesion
import empleados
import doctores
import paciente
import cita
import medicamentos
import consultas


def crear_imagen_diagnostico(ventana):
    ancho, alto = 240, 150
    img = tk.PhotoImage(master=ventana, width=ancho, height=alto)
    img.put("#e8f1f8", to=(0, 0, ancho, alto))
    img.put("#1f4e78", to=(0, 0, ancho, 4))
    img.put("#1f4e78", to=(0, alto - 4, ancho, alto))
    img.put("#1f4e78", to=(0, 0, 4, alto))
    img.put("#1f4e78", to=(ancho - 4, 0, ancho, alto))
    img.put("#1f4e78", to=(105, 32, 135, 118))
    img.put("#1f4e78", to=(77, 60, 163, 90))
    return img


def abrir_ventana_principal(raiz, usuario_logeado, rol, callback_login):
    ventana = tk.Toplevel(raiz)
    ventana.title("Ventana Principal - Núcleo de Diagnóstico")
    ventana.geometry("760x460")

    def cerrar_sesion():
        confirmar = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Estás seguro de que deseas cerrar sesión?",
            parent=ventana
        )
        if confirmar:
            cerrar_conexion()
            sesion.cerrar()
            ventana.destroy()
            callback_login()

    ventana.protocol("WM_DELETE_WINDOW", cerrar_sesion)

    # Barra superior con botón CERRAR SESIÓN y el nombre completo del usuario
    barra_superior = tk.Frame(ventana, bg="#1f4e78", height=38)
    barra_superior.pack(fill="x")

    tk.Button(
        barra_superior,
        text="CERRAR SESIÓN",
        bg="#c0392b",
        fg="white",
        font=("Arial", 9, "bold"),
        padx=10,
        pady=3,
        cursor="hand2",
        command=cerrar_sesion
    ).pack(side="left", padx=12, pady=5)

    tk.Label(
        barra_superior,
        text=f"Hola, {usuario_logeado}",
        bg="#1f4e78",
        fg="white",
        font=("Arial", 11, "bold"),
        padx=15
    ).pack(side="right", pady=6)

    # Barra de menús separada por tipo de usuario
    barra_menu = tk.Menu(ventana)

    if rol == "empleado":
        menu_pacientes = tk.Menu(barra_menu, tearoff=0)
        menu_pacientes.add_command(
            label="Insertar (dar de alta)",
            command=lambda: paciente.insertar_paciente(ventana)
        )
        menu_pacientes.add_command(
            label="Consultas Generales",
            command=lambda: paciente.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="PACIENTES", menu=menu_pacientes)

        menu_citas = tk.Menu(barra_menu, tearoff=0)
        menu_citas.add_command(
            label="Registrar cita",
            command=lambda: cita.registrar_cita(ventana)
        )
        menu_citas.add_command(
            label="Consultas generales",
            command=lambda: cita.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="CITAS", menu=menu_citas)

    elif rol == "doctor":
        menu_citas = tk.Menu(barra_menu, tearoff=0)
        menu_citas.add_command(
            label="Ver citas",
            command=lambda: cita.ver_citas_doctor(ventana)
        )
        barra_menu.add_cascade(label="CITAS", menu=menu_citas)

        menu_pacientes = tk.Menu(barra_menu, tearoff=0)
        menu_pacientes.add_command(
            label="Ver paciente",
            command=lambda: cita.ver_paciente_proxima_cita(ventana)
        )
        barra_menu.add_cascade(label="PACIENTES", menu=menu_pacientes)

        menu_consultas = tk.Menu(barra_menu, tearoff=0)
        menu_consultas.add_command(
            label="Registrar consulta (diagnóstico)",
            command=lambda: consultas.registrar_consulta(ventana)
        )
        menu_consultas.add_command(
            label="Ver historial de consultas",
            command=lambda: consultas.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="CONSULTAS", menu=menu_consultas)

    elif rol == "admin":
        menu_doctores = tk.Menu(barra_menu, tearoff=0)
        menu_doctores.add_command(
            label="Insertar doctor",
            command=lambda: doctores.insertar_doctor(ventana)
        )
        menu_doctores.add_command(
            label="Consultas generales",
            command=lambda: doctores.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="DOCTORES", menu=menu_doctores)

        menu_empleados = tk.Menu(barra_menu, tearoff=0)
        menu_empleados.add_command(
            label="Insertar (agregar)",
            command=lambda: empleados.insertar_empleado(ventana)
        )
        menu_empleados.add_command(
            label="Consultas Generales",
            command=lambda: empleados.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="EMPLEADOS", menu=menu_empleados)

        menu_pacientes = tk.Menu(barra_menu, tearoff=0)
        menu_pacientes.add_command(
            label="Insertar (dar de alta)",
            command=lambda: paciente.insertar_paciente(ventana)
        )
        menu_pacientes.add_command(
            label="Consultas Generales",
            command=lambda: paciente.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="PACIENTES", menu=menu_pacientes)

        menu_medicamentos = tk.Menu(barra_menu, tearoff=0)
        menu_medicamentos.add_command(
            label="Insertar (dar de alta)",
            command=lambda: medicamentos.insertar_medicamento(ventana)
        )
        menu_medicamentos.add_command(
            label="Consultas generales",
            command=lambda: medicamentos.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="MEDICAMENTOS", menu=menu_medicamentos)

        menu_consultas = tk.Menu(barra_menu, tearoff=0)
        menu_consultas.add_command(
            label="Registrar consulta",
            command=lambda: consultas.registrar_consulta(ventana)
        )
        menu_consultas.add_command(
            label="Consultas generales",
            command=lambda: consultas.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="CONSULTAS", menu=menu_consultas)

        menu_citas = tk.Menu(barra_menu, tearoff=0)
        menu_citas.add_command(
            label="Registrar cita",
            command=lambda: cita.registrar_cita(ventana)
        )
        menu_citas.add_command(
            label="Modificar cita",
            command=lambda: cita.modificar_cita(ventana)
        )
        menu_citas.add_command(
            label="Consultas generales",
            command=lambda: cita.consultas_generales(ventana)
        )
        barra_menu.add_cascade(label="CITAS", menu=menu_citas)

    ventana.config(menu=barra_menu)

    # Contenido central con imagen empotrada
    contenedor = tk.Frame(ventana)
    contenedor.pack(expand=True)

    tk.Label(
        contenedor,
        text="SISTEMA DE GESTIÓN\nNÚCLEO DE DIAGNÓSTICO",
        font=("Arial", 15, "bold"),
        fg="#1f4e78"
    ).pack(pady=15)

    ventana.imagen_diagnostico = crear_imagen_diagnostico(ventana)
    tk.Label(contenedor, image=ventana.imagen_diagnostico).pack(pady=10)