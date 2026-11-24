"""Agenda semanal de un doctor (lunes a domingo) en formato de tabla."""
import datetime
import tkinter as tk
from tkinter import messagebox
from conexion import obtener_conexion
import sesion

HORA_INICIO = 9            # primera franja: 9:00 a 10:00 am
HORA_FIN = 20              # última franja: 7:00 a 8:00 pm (la jornada termina a las 8 pm)
HORAS_COMIDA = (14, 15)    # 2:00 a 4:00 pm: hora de comida del doctor

DIAS = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
AZUL = "#1f4e78"

COLOR_ENCABEZADO = "#d9e2f3"
COLOR_LIBRE = "#ffffff"
COLOR_LIBRE_HOVER = "#e2f0d9"
COLOR_OCUPADO = "#f8cbad"
COLOR_COMIDA = "#fff2cc"
COLOR_PASADO = "#eeeeee"


def _hora12(h):
    return h % 12 or 12


def etiqueta_franja(h):
    """9 -> '9:00 A 10:00', 12 -> '12:00 A 1:00', 19 -> '7:00 A 8:00'."""
    return f"{_hora12(h)}:00 A {_hora12(h + 1)}:00"


def _citas_semana(id_doctor, ppk, lunes):
    """Devuelve {(fecha, hora_entera): [nombres de pacientes]} de lunes a domingo."""
    domingo = lunes + datetime.timedelta(days=6)
    conexion = obtener_conexion()
    with conexion.cursor() as cur:
        cur.execute(
            f"SELECT c.fecha, c.hora, p.nombre FROM cita c "
            f"JOIN paciente p ON p.{ppk} = c.id_paciente "
            f"WHERE c.id_doctor = %s AND c.fecha BETWEEN %s AND %s",
            (id_doctor, lunes, domingo),
        )
        filas = cur.fetchall()
    ocupadas = {}
    for fecha, hora, nombre in filas:
        ocupadas.setdefault((fecha, hora.hour), []).append(nombre)
    return ocupadas


def ver_agenda_semana(padre, id_doctor, nombre_doctor, ppk, fecha_inicial=None, al_elegir=None,
                      permitir_pasado=False):
    """Abre la agenda de la semana. Si se pasa al_elegir(fecha, hora), al hacer clic en un
    horario libre se llama a esa función (para llenar el formulario de la cita)."""
    hoy = datetime.date.today()
    base = fecha_inicial or hoy
    lunes = base - datetime.timedelta(days=base.weekday())
    estado = {"lunes": lunes}

    win = tk.Toplevel(padre)
    win.title(f"Agenda de {nombre_doctor} - Usuario: {sesion.obtener()}")
    win.geometry("960x610")
    sesion.poner_saludo(win)

    tk.Label(win, text=f"AGENDA DEL DOCTOR {nombre_doctor.upper()} (SEMANA)",
             font=("Arial", 12, "bold"), fg=AZUL).pack()

    nav = tk.Frame(win)
    nav.pack(pady=6)
    tk.Button(nav, text="< Semana anterior", command=lambda: mover(-7)).pack(side=tk.LEFT)
    etiqueta_semana = tk.Label(nav, font=("Arial", 10, "bold"), width=30)
    etiqueta_semana.pack(side=tk.LEFT, padx=8)
    tk.Button(nav, text="Semana siguiente >", command=lambda: mover(7)).pack(side=tk.LEFT)

    cuadro = tk.Frame(win, bg="#7f7f7f")
    cuadro.pack(padx=10)

    leyenda = tk.Frame(win)
    leyenda.pack(pady=8)
    for color, texto in [(COLOR_LIBRE, "Libre"), (COLOR_OCUPADO, "Ocupado"),
                         (COLOR_COMIDA, "Comida"), (COLOR_PASADO, "Día pasado")]:
        tk.Label(leyenda, text="    ", bg=color, relief="solid", bd=1).pack(side=tk.LEFT, padx=(10, 3))
        tk.Label(leyenda, text=texto).pack(side=tk.LEFT)
    if al_elegir:
        tk.Label(win, text="Haz clic en un horario libre para llenar la fecha y la hora de la cita.",
                 fg=AZUL).pack()

    def celda(fila, columna, texto, bg, negrita=False):
        lbl = tk.Label(cuadro, text=texto, bg=bg, width=12, height=2, wraplength=88,
                       relief="solid", bd=1, font=("Arial", 9, "bold" if negrita else "normal"))
        lbl.grid(row=fila, column=columna)
        return lbl

    def elegir(dia, hora):
        if al_elegir:
            al_elegir(dia, datetime.time(hora, 0))
        win.destroy()

    def dibujar():
        for w in cuadro.winfo_children():
            w.destroy()
        lunes = estado["lunes"]
        try:
            ocupadas = _citas_semana(id_doctor, ppk, lunes)
        except Exception as error:
            obtener_conexion().rollback()
            messagebox.showerror("Error", str(error))
            return

        domingo = lunes + datetime.timedelta(days=6)
        etiqueta_semana.config(
            text=f"{lunes.day}/{MESES[lunes.month - 1]} al {domingo.day}/{MESES[domingo.month - 1]} "
                 f"{domingo.year}")

        celda(0, 0, "HORARIO", COLOR_ENCABEZADO, True)
        for i, nombre in enumerate(DIAS):
            dia = lunes + datetime.timedelta(days=i)
            celda(0, i + 1, f"{nombre}\n{dia.day}/{MESES[dia.month - 1]}", COLOR_ENCABEZADO, True)

        for fila, h in enumerate(range(HORA_INICIO, HORA_FIN), start=1):
            celda(fila, 0, etiqueta_franja(h), "#f2f2f2")
            for i in range(7):
                dia = lunes + datetime.timedelta(days=i)
                if h in HORAS_COMIDA:
                    celda(fila, i + 1, "COMIDA", COLOR_COMIDA)
                elif (dia, h) in ocupadas:
                    celda(fila, i + 1, ", ".join(ocupadas[(dia, h)]), COLOR_OCUPADO)
                elif dia < hoy and not permitir_pasado:
                    celda(fila, i + 1, "", COLOR_PASADO)
                else:
                    lbl = celda(fila, i + 1, "", COLOR_LIBRE)
                    if al_elegir:
                        lbl.config(cursor="hand2")
                        lbl.bind("<Enter>", lambda e, w=lbl: w.config(bg=COLOR_LIBRE_HOVER))
                        lbl.bind("<Leave>", lambda e, w=lbl: w.config(bg=COLOR_LIBRE))
                        lbl.bind("<Button-1>", lambda e, d=dia, hh=h: elegir(d, hh))

    def mover(dias):
        estado["lunes"] += datetime.timedelta(days=dias)
        dibujar()

    dibujar()