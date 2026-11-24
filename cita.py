"""Módulo de CITAS: registrar, modificar y consultar citas."""
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import obtener_conexion
from esquema import columna_pk
from tabla import mostrar_consulta
from calendario import SelectorFecha, SelectorHora
from agenda import (ver_agenda_semana, etiqueta_franja,
                    HORA_INICIO, HORA_FIN, HORAS_COMIDA)
import sesion

# True = se puede agendar en cualquier fecha (pasada o futura). False = solo desde hoy.
PERMITIR_FECHAS_PASADAS = True
FECHA_MINIMA = datetime.date.min if PERMITIR_FECHAS_PASADAS else None


# ------------------------------------------------------------------
# Funciones de apoyo
# ------------------------------------------------------------------
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


def _nombre_de(opcion):
    return opcion.split(" - ", 1)[1]


def _horas_ocupadas(id_doctor, fecha, excluir_cita=None):
    """Horas enteras (9, 10, ...) en las que el doctor ya tiene cita ese día."""
    consulta = "SELECT hora FROM cita WHERE id_doctor = %s AND fecha = %s"
    params = [id_doctor, fecha]
    if excluir_cita is not None:
        consulta += " AND id_cita <> %s"
        params.append(excluir_cita)
    with obtener_conexion().cursor() as cur:
        cur.execute(consulta, params)
        return {fila[0].hour for fila in cur.fetchall()}


def _horas_libres(ocupadas):
    libres = [f"{h:02d}:00" for h in range(HORA_INICIO, HORA_FIN)
              if h not in ocupadas and h not in HORAS_COMIDA]
    return ", ".join(libres) or "ninguna"


def _paciente_ocupado(id_paciente, fecha, hora, excluir_cita=None):
    """True si el paciente ya tiene otra cita en esa misma franja horaria."""
    inicio = datetime.time(hora.hour, 0)
    fin = datetime.time(hora.hour + 1, 0) if hora.hour < 23 else datetime.time(23, 59, 59)
    consulta = ("SELECT 1 FROM cita WHERE id_paciente = %s AND fecha = %s "
                "AND hora >= %s AND hora < %s")
    params = [id_paciente, fecha, inicio, fin]
    if excluir_cita is not None:
        consulta += " AND id_cita <> %s"
        params.append(excluir_cita)
    with obtener_conexion().cursor() as cur:
        cur.execute(consulta, params)
        return cur.fetchone() is not None


def evaluar_disponibilidad(nombre_doc, id_doc, fecha, hora, excluir_cita=None):
    """Devuelve (se_puede, texto). Reglas: 9:00 a 20:00, sin la hora de comida
    y sin empalmar con otra cita del doctor (excluir_cita = cita que se está cambiando)."""
    cuando = f"el {fecha.strftime('%d/%m/%Y')} a las {hora.strftime('%H:%M')}"
    if not (HORA_INICIO <= hora.hour < HORA_FIN):
        return False, (f"NO se puede.\n\nLa hora {hora.strftime('%H:%M')} está fuera del "
                       f"horario de atención ({HORA_INICIO}:00 a {HORA_FIN}:00).")

    ocupadas = _horas_ocupadas(id_doc, fecha, excluir_cita)
    libres = f"Horas libres ese día: {_horas_libres(ocupadas)}"
    if hora.hour in HORAS_COMIDA:
        return False, (f"NO se puede.\n\n{nombre_doc} está en su hora de comida "
                       f"({etiqueta_franja(HORAS_COMIDA[0]).split(' A ')[0]} a "
                       f"{etiqueta_franja(HORAS_COMIDA[-1]).split(' A ')[1]}).\n\n{libres}")
    if hora.hour in ocupadas:
        return False, (f"NO se puede.\n\n{nombre_doc} ya tiene una cita en la franja de "
                       f"{etiqueta_franja(hora.hour)} {fecha.strftime('el %d/%m/%Y')}.\n\n{libres}")
    return True, f"SÍ se puede.\n\n{nombre_doc} está libre {cuando}.\n\n{libres}"


def _validar_fecha_hora(fecha, hora):
    if not fecha or not hora:
        messagebox.showwarning("Faltan datos",
                               "Elige la fecha en el calendario y la hora en el horario.")
        return False
    if not PERMITIR_FECHAS_PASADAS and fecha < datetime.date.today():
        messagebox.showwarning("Fecha inválida", "No se puede agendar en una fecha pasada.")
        return False
    return True


def _abrir_agenda(win, cb_doctor, ppk, selector_fecha, selector_hora):
    if not cb_doctor.get():
        messagebox.showwarning("Faltan datos", "Elige al doctor para ver su agenda.")
        return

    def llenar(fecha, hora):
        selector_fecha.set(fecha)
        selector_hora.set(hora)

    ver_agenda_semana(win, _id_de(cb_doctor.get()), _nombre_de(cb_doctor.get()), ppk,
                      fecha_inicial=selector_fecha.get(), al_elegir=llenar,
                      permitir_pasado=PERMITIR_FECHAS_PASADAS)


def _mostrar_disponibilidad(libre, texto):
    (messagebox.showinfo if libre else messagebox.showwarning)("Disponibilidad", texto)


# ------------------------------------------------------------------
# Consultas generales
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Registrar cita
# ------------------------------------------------------------------
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
    win.geometry("420x580")
    sesion.poner_saludo(win)

    tk.Label(win, text="Paciente:").pack(pady=(6, 0))
    cb_paciente = ttk.Combobox(win, values=pacientes, state="readonly", width=40)
    cb_paciente.pack()

    tk.Label(win, text="Doctor:").pack(pady=(10, 0))
    cb_doctor = ttk.Combobox(win, values=doctores, state="readonly", width=40)
    cb_doctor.pack()

    tk.Label(win, text="Fecha:").pack(pady=(10, 0))
    selector_fecha = SelectorFecha(win, FECHA_MINIMA)
    selector_fecha.pack()

    tk.Label(win, text="Hora:").pack(pady=(10, 0))
    selector_hora = SelectorHora(win, HORA_INICIO, HORA_FIN)
    selector_hora.pack()

    def verificar():
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor.")
            return
        fecha, hora = selector_fecha.get(), selector_hora.get()
        if not _validar_fecha_hora(fecha, hora):
            return
        try:
            libre, texto = evaluar_disponibilidad(_nombre_de(cb_doctor.get()),
                                                  _id_de(cb_doctor.get()), fecha, hora)
        except Exception as error:
            obtener_conexion().rollback()
            messagebox.showerror("Error", str(error))
            return
        _mostrar_disponibilidad(libre, texto)

    def guardar():
        if not cb_paciente.get():
            messagebox.showwarning("Faltan datos", "Elige al paciente.")
            return
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor.")
            return
        fecha, hora = selector_fecha.get(), selector_hora.get()
        if not _validar_fecha_hora(fecha, hora):
            return
        id_pac, id_doc = _id_de(cb_paciente.get()), _id_de(cb_doctor.get())
        conexion = obtener_conexion()
        try:
            libre, texto = evaluar_disponibilidad(_nombre_de(cb_doctor.get()), id_doc, fecha, hora)
            if not libre:
                messagebox.showwarning("No se puede registrar la cita", texto)
                return
            if _paciente_ocupado(id_pac, fecha, hora):
                messagebox.showwarning("No se puede registrar la cita",
                                       "El paciente ya tiene otra cita en esa misma franja horaria.")
                return
            with conexion.cursor() as cur:
                cur.execute(
                    "INSERT INTO cita (id_paciente, id_doctor, fecha, hora) "
                    "VALUES (%s, %s, %s, %s) RETURNING id_cita",
                    (id_pac, id_doc, fecha, hora))
                id_cita = cur.fetchone()[0]
            conexion.commit()
            etiqueta_id.config(text=f"ID cita: {id_cita}")
            messagebox.showinfo("Cita registrada",
                                f"Cita registrada correctamente.\n\nID cita: {id_cita}\n"
                                f"Fecha: {fecha.strftime('%d/%m/%Y')}\n"
                                f"Hora: {hora.strftime('%H:%M')}", parent=win)
            selector_fecha.clear()
            selector_hora.clear()
            cb_paciente.set("")
            cb_doctor.set("")
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al registrar la cita", str(error))

    tk.Button(win, text="Ver agenda del doctor", width=24,
              command=lambda: _abrir_agenda(win, cb_doctor, ppk, selector_fecha, selector_hora)
              ).pack(pady=(18, 4))
    tk.Button(win, text="Verificar disponibilidad", width=24, command=verificar).pack(pady=4)
    tk.Button(win, text="Registrar cita", width=24, command=guardar).pack(pady=4)
    etiqueta_id = tk.Label(win, text="", font=("Arial", 13, "bold"), fg="#1f4e78")
    etiqueta_id.pack(pady=(12, 0))


# ------------------------------------------------------------------
# Modificar cita (actualizar)
# ------------------------------------------------------------------
def modificar_cita(padre):
    ppk, pacientes = _opciones("paciente")
    dpk, doctores = _opciones("doctor")
    if pacientes is None or doctores is None:
        return
    if not pacientes or not doctores:
        messagebox.showwarning("Faltan datos",
                               "Debe haber al menos un paciente y un doctor registrados.")
        return

    win = tk.Toplevel(padre)
    win.title(f"Modificar cita - Usuario: {sesion.obtener()}")
    win.geometry("480x660")
    sesion.poner_saludo(win)

    citas = {}   # texto de la lista -> (id_cita, id_doctor, fecha, hora)

    tk.Label(win, text="Paciente:").pack(pady=(6, 0))
    cb_paciente = ttk.Combobox(win, values=pacientes, state="readonly", width=44)
    cb_paciente.pack()

    tk.Label(win, text="Cita que desea cambiar:").pack(pady=(10, 0))
    cb_cita = ttk.Combobox(win, values=[], state="readonly", width=44)
    cb_cita.pack()

    tk.Label(win, text="NUEVOS DATOS DE LA CITA", font=("Arial", 10, "bold"),
             fg="#1f4e78").pack(pady=(16, 0))

    tk.Label(win, text="Doctor:").pack(pady=(6, 0))
    cb_doctor = ttk.Combobox(win, values=doctores, state="readonly", width=44)
    cb_doctor.pack()

    tk.Label(win, text="Fecha:").pack(pady=(10, 0))
    selector_fecha = SelectorFecha(win, FECHA_MINIMA)
    selector_fecha.pack()

    tk.Label(win, text="Hora:").pack(pady=(10, 0))
    selector_hora = SelectorHora(win, HORA_INICIO, HORA_FIN)
    selector_hora.pack()

    def limpiar_nuevos_datos():
        cb_doctor.set("")
        selector_fecha.clear()
        selector_hora.clear()

    def cargar_citas(_evento=None):
        """Llena la lista con las citas del paciente elegido."""
        citas.clear()
        cb_cita.set("")
        cb_cita["values"] = []
        limpiar_nuevos_datos()
        if not cb_paciente.get():
            return
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cur:
                cur.execute(
                    "SELECT c.id_cita, c.id_doctor, c.fecha, c.hora, d.nombre "
                    f"FROM cita c JOIN doctor d ON d.{dpk} = c.id_doctor "
                    "WHERE c.id_paciente = %s ORDER BY c.fecha, c.hora",
                    (_id_de(cb_paciente.get()),))
                filas = cur.fetchall()
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error", str(error))
            return
        for id_cita, id_doc, fecha, hora, nombre_doc in filas:
            texto = (f"ID {id_cita} - {fecha.strftime('%d/%m/%Y')} "
                     f"{hora.strftime('%H:%M')} - {nombre_doc}")
            citas[texto] = (id_cita, id_doc, fecha, hora)
        cb_cita["values"] = list(citas.keys())
        if not citas:
            messagebox.showinfo("Sin citas", "Este paciente no tiene citas registradas.")

    def elegir_cita(_evento=None):
        """Al elegir la cita, se llenan los datos actuales para cambiar solo lo necesario."""
        datos = citas.get(cb_cita.get())
        if not datos:
            return
        _, id_doc, fecha, hora = datos
        cb_doctor.set(next((o for o in doctores if _id_de(o) == id_doc), ""))
        selector_fecha.set(fecha)
        selector_hora.set(hora)

    cb_paciente.bind("<<ComboboxSelected>>", cargar_citas)
    cb_cita.bind("<<ComboboxSelected>>", elegir_cita)

    def id_cita_elegida():
        datos = citas.get(cb_cita.get())
        return datos[0] if datos else None

    def verificar():
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor.")
            return
        fecha, hora = selector_fecha.get(), selector_hora.get()
        if not _validar_fecha_hora(fecha, hora):
            return
        try:
            libre, texto = evaluar_disponibilidad(_nombre_de(cb_doctor.get()),
                                                  _id_de(cb_doctor.get()), fecha, hora,
                                                  excluir_cita=id_cita_elegida())
        except Exception as error:
            obtener_conexion().rollback()
            messagebox.showerror("Error", str(error))
            return
        _mostrar_disponibilidad(libre, texto)

    def actualizar():
        if not cb_paciente.get():
            messagebox.showwarning("Faltan datos", "Elige al paciente.")
            return
        id_cita = id_cita_elegida()
        if id_cita is None:
            messagebox.showwarning("Faltan datos", "Elige la cita que desea cambiar.")
            return
        if not cb_doctor.get():
            messagebox.showwarning("Faltan datos", "Elige al doctor.")
            return
        fecha, hora = selector_fecha.get(), selector_hora.get()
        if not _validar_fecha_hora(fecha, hora):
            return

        id_pac, id_doc = _id_de(cb_paciente.get()), _id_de(cb_doctor.get())
        nombre_doc = _nombre_de(cb_doctor.get())
        conexion = obtener_conexion()
        try:
            libre, texto = evaluar_disponibilidad(nombre_doc, id_doc, fecha, hora,
                                                  excluir_cita=id_cita)
            if not libre:
                messagebox.showwarning("No se puede cambiar la cita", texto)
                return
            if _paciente_ocupado(id_pac, fecha, hora, excluir_cita=id_cita):
                messagebox.showwarning("No se puede cambiar la cita",
                                       "El paciente ya tiene otra cita en esa misma franja horaria.")
                return
            nueva = f"{fecha.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')} - {nombre_doc}"
            if not messagebox.askyesno("Confirmar cambio",
                                       f"¿Cambiar la cita?\n\nCita actual: {cb_cita.get()}\n"
                                       f"Cita nueva:   {nueva}", parent=win):
                return
            with conexion.cursor() as cur:
                cur.execute("UPDATE cita SET id_doctor = %s, fecha = %s, hora = %s "
                            "WHERE id_cita = %s", (id_doc, fecha, hora, id_cita))
            conexion.commit()
            messagebox.showinfo("Cita actualizada",
                                f"ID cita: {id_cita}\nLa cita se cambió a:\n{nueva}", parent=win)
            cargar_citas()          # refresca la lista con los datos nuevos
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al actualizar la cita", str(error))

    tk.Button(win, text="Ver agenda del doctor", width=24,
              command=lambda: _abrir_agenda(win, cb_doctor, ppk, selector_fecha, selector_hora)
              ).pack(pady=(18, 4))
    tk.Button(win, text="Verificar disponibilidad", width=24, command=verificar).pack(pady=4)
    tk.Button(win, text="Actualizar cita", width=24, command=actualizar).pack(pady=4)