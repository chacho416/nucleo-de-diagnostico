"""Módulo de CITAS: registrar cita (con agenda y verificación de disponibilidad)."""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import obtener_conexion
from esquema import columna_pk
from tabla import mostrar_consulta
from calendario import SelectorFecha, SelectorHora
import sesion

HORA_INICIO = 8     # horario de atención: de 08:00 ...
HORA_FIN = 18       # ... a 17:00


def _opciones(tabla):
    """Devuelve (nombre_de_la_pk, ['1 - NOMBRE', ...]) de una tabla; lista None si hubo error."""
    conexion = obtener_conexion()
    pk = columna_pk(tabla) or f"id_{tabla}"
    try:
        with conexion.cursor() as cur:
            cur.execute(f"SELECT {pk}, nombre FROM {tabla} ORDER BY nombre")
            return pk, [f"{i} - {n}" for i, n in cur.fetchall()]
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", f"No pude leer la tabla {tabla}:\n{error}")
        return pk, None


def _id_de(opcion):
    return int(opcion.split(" - ")[0])


def _horas_ocupadas(id_doctor, fecha):
    conexion = obtener_conexion()
    with conexion.cursor() as cur:
        cur.execute("SELECT hora FROM cita WHERE id_doctor = %s AND fecha = %s",
                    (id_doctor, fecha))
        return {fila[0] for fila in cur.fetchall()}


def _horas_libres(ocupadas):
    libres = [datetime.time(h, 0) for h in range(HORA_INICIO, HORA_FIN)
              if datetime.time(h, 0) not in ocupadas]
    return ", ".join(h.strftime("%H:%M") for h in libres) or "ninguna"


def consultas_generales(padre):
    ppk = columna_pk("paciente") or "id_paciente"
    dpk = columna_pk("doctor") or "id_doctor"
    consulta = (
        "SELECT c.id_cita, c.fecha, c.hora, p.nombre AS paciente, d.nombre AS doctor "
        f"FROM cita c JOIN paciente p ON p.{ppk} = c.id_paciente "
        f"JOIN doctor d ON d.{dpk} = c.id_doctor "
        "ORDER BY c.fecha, c.hora"
    )
    mostrar_consulta(padre, "Consultas generales - Citas", consulta)


def registrar_cita(padre):
    ppk, pacientes = _opciones("paciente")
    dpk, doctores = _opciones("doctor")
    if pacientes is None or doctores is None:
        return
    if not pacientes or not doctores:
        messagebox.showwarning("Faltan datos",
                               "Debe haber al menos un paciente y un doctor registrados.")
        return

    win = tk.Toplevel(padre)
    win.title(f"Registrar cita - Usuario: {sesion.obtener()}")
    win.geometry("420x510")
    sesion.poner_saludo(win)

    tk.Label(win, text="Paciente:").pack(pady=(6, 0))
    cb_paciente = ttk.Combobox(win, values=pacientes, state="readonly", width=40)
    cb_paciente.pack()

    tk.Label(win, text="Doctor:").pack(pady=(10, 0))
    cb_doctor = ttk.Combobox(win, values=doctores, state="readonly", width=40)
    cb_doctor.pack()

    tk.Label(win, text="Fecha:").pack(pady=(10, 0))
    sel_fecha = SelectorFecha(win)
    sel_fecha.pack(pady=(2, 0))

    tk.Label(win, text="Hora:").pack(pady=(10, 0))
    sel_hora = SelectorHora(win, hora_inicio=HORA_INICIO, hora_fin=HORA_FIN)
    sel_hora.pack(pady=(2, 0))

    def leer(requiere_paciente):
        """Valida el formulario. Devuelve (id_paciente, id_doctor, fecha, hora) o None."""
        if requiere_paciente and not cb_paciente.get():
            messagebox.showwarning("Faltan datos", "Elige al paciente.")
            return None
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor.")
            return None
        fecha = sel_fecha.get()
        hora = sel_hora.get()
        if not fecha:
            messagebox.showwarning("Faltan datos", "Elige una fecha en el calendario.")
            return None
        if not hora:
            messagebox.showwarning("Faltan datos", "Elige una hora en el horario.")
            return None
        if fecha < datetime.date.today():
            messagebox.showwarning("Fecha inválida", "No se puede agendar en una fecha pasada.")
            return None
        id_pac = _id_de(cb_paciente.get()) if cb_paciente.get() else None
        return id_pac, _id_de(cb_doctor.get()), fecha, hora

    def mensaje_disponibilidad(id_doc, fecha, hora):
        ocupadas = _horas_ocupadas(id_doc, fecha)
        libre = hora not in ocupadas
        nombre_doc = cb_doctor.get().split(" - ", 1)[1]
        cuando = f"el {fecha.strftime('%d/%m/%Y')} a las {hora.strftime('%H:%M')}"
        if libre:
            texto = f"SÍ se puede.\n\n{nombre_doc} está libre {cuando}."
        else:
            texto = (f"NO se puede.\n\n{nombre_doc} ya tiene una cita {cuando}.\n\n"
                     f"Horas libres ese día: {_horas_libres(ocupadas)}")
        return libre, texto

    def verificar():
        datos = leer(requiere_paciente=False)
        if not datos:
            return
        _, id_doc, fecha, hora = datos
        try:
            libre, texto = mensaje_disponibilidad(id_doc, fecha, hora)
        except Exception as error:
            obtener_conexion().rollback()
            messagebox.showerror("Error", str(error))
            return
        (messagebox.showinfo if libre else messagebox.showwarning)("Disponibilidad", texto)

    def ver_agenda():
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor para ver su agenda.")
            return
        id_doc = _id_de(cb_doctor.get())
        nombre_doc = cb_doctor.get().split(" - ", 1)[1]
        fecha = sel_fecha.get()
        consulta = ("SELECT c.id_cita, c.fecha, c.hora, p.nombre AS paciente "
                    f"FROM cita c JOIN paciente p ON p.{ppk} = c.id_paciente "
                    "WHERE c.id_doctor = %s ")
        params = [id_doc]
        titulo = f"Agenda - {nombre_doc}"
        if fecha:
            consulta += "AND c.fecha = %s "
            params.append(fecha)
            titulo += f" ({fecha.strftime('%d/%m/%Y')})"
        else:
            consulta += "AND c.fecha >= CURRENT_DATE "
            titulo += " (próximas citas)"
        consulta += "ORDER BY c.fecha, c.hora"
        mostrar_consulta(win, titulo, consulta, params)

    def guardar():
        datos = leer(requiere_paciente=True)
        if not datos:
            return
        id_pac, id_doc, fecha, hora = datos
        conexion = obtener_conexion()
        try:
            libre, texto = mensaje_disponibilidad(id_doc, fecha, hora)
            if not libre:
                messagebox.showwarning("No se puede registrar la cita", texto)
                return
            with conexion.cursor() as cur:
                cur.execute("SELECT 1 FROM cita WHERE id_paciente = %s AND fecha = %s AND hora = %s",
                            (id_pac, fecha, hora))
                if cur.fetchone():
                    messagebox.showwarning("No se puede registrar la cita",
                                           "El paciente ya tiene otra cita a esa misma fecha y hora.")
                    return
                cur.execute(
                    "INSERT INTO cita (id_paciente, id_doctor, fecha, hora) VALUES (%s, %s, %s, %s)",
                    (id_pac, id_doc, fecha, hora))
            conexion.commit()
            messagebox.showinfo("Cita registrada",
                                f"Cita registrada para el {fecha.strftime('%d/%m/%Y')} "
                                f"a las {hora.strftime('%H:%M')}.")
            sel_fecha.clear()
            sel_hora.clear()
            cb_paciente.set("")
            cb_doctor.set("")
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al registrar la cita", str(error))

    tk.Button(win, text="Ver agenda del doctor", width=24, command=ver_agenda).pack(pady=(18, 4))
    tk.Button(win, text="Verificar disponibilidad", width=24, command=verificar).pack(pady=4)
    tk.Button(win, text="Registrar cita", width=24, command=guardar).pack(pady=4)