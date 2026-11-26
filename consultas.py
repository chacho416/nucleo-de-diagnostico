"""Módulo de CONSULTAS MÉDICAS: registro de diagnóstico, historial interactivo y receta PDF."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from conexion import obtener_conexion
from esquema import columna_pk
import sesion


def _opciones_citas():
    """Si entra un doctor, carga solo sus citas; si es admin, carga todas."""
    conexion = obtener_conexion()
    ppk = columna_pk("paciente") or "id_paciente"
    dpk = columna_pk("doctor") or "id_doctor"
    id_doc = sesion.obtener_id()

    try:
        with conexion.cursor() as cur:
            if id_doc is not None:
                cur.execute(
                    "SELECT c.id_cita, c.fecha, c.hora, p.nombre "
                    f"FROM cita c JOIN paciente p ON p.{ppk} = c.id_paciente "
                    "WHERE c.id_doctor = %s "
                    "ORDER BY c.fecha DESC, c.hora DESC",
                    (id_doc,),
                )
                return [
                    f"{cid} - {f.strftime('%d/%m/%Y')} {h.strftime('%H:%M')} | Pac: {pac}"
                    for cid, f, h, pac in cur.fetchall()
                ]
            else:
                cur.execute(
                    "SELECT c.id_cita, c.fecha, c.hora, p.nombre, d.nombre "
                    f"FROM cita c JOIN paciente p ON p.{ppk} = c.id_paciente "
                    f"JOIN doctor d ON d.{dpk} = c.id_doctor "
                    "ORDER BY c.fecha DESC, c.hora DESC"
                )
                return [
                    f"{cid} - {f.strftime('%d/%m/%Y')} {h.strftime('%H:%M')} | Pac: {pac} | Dr: {doc}"
                    for cid, f, h, pac, doc in cur.fetchall()
                ]
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", f"No pude leer las citas:\n{error}")
        return None


def _opciones_medicamentos():
    conexion = obtener_conexion()
    pk = columna_pk("medicamento") or "id_medicamento"
    try:
        with conexion.cursor() as cur:
            cur.execute(
                f"SELECT {pk}, nombre, presentacion, via_administracion "
                "FROM medicamento ORDER BY nombre"
            )
            return [
                f"{mid} - {nom} ({pres}, vía {via})"
                for mid, nom, pres, via in cur.fetchall()
            ]
    except Exception as error:
        conexion.rollback()
        messagebox.showerror("Error", f"No pude leer los medicamentos:\n{error}")
        return None


def _id_de(opcion):
    return int(opcion.split(" - ")[0])


def _crear_pdf_receta(ruta_pdf, datos):
    """Genera el archivo físico receta.pdf en formato Carta con los datos de la consulta."""
    def esc(texto):
        return (
            str(texto)
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    def envolver(texto, ancho_max=82):
        lineas = []
        for parrafo in str(texto).splitlines():
            palabras = parrafo.split(" ")
            actual = ""
            for p in palabras:
                if len(actual) + len(p) + 1 <= ancho_max:
                    actual = f"{actual} {p}".strip()
                else:
                    if actual:
                        lineas.append(actual)
                    actual = p
            lineas.append(actual)
        return lineas or [""]

    ops = []

    # Encabezado institucional
    ops.append("0.122 0.306 0.471 rg")
    ops.append("45 705 522 52 re f")
    ops.append("1 1 1 rg")
    ops.append("BT /F2 16 Tf 60 735 Td (NUCLEO DE DIAGNOSTICO MEDICO) Tj ET")
    ops.append("BT /F1 10 Tf 60 718 Td (RECETA MEDICA OFICIAL) Tj ET")

    # Folio y fecha
    ops.append("0 0 0 rg")
    ops.append(f"BT /F2 10 Tf 415 685 Td (Consulta ID: {esc(datos['id_consulta'])}) Tj ET")
    ops.append(f"BT /F1 10 Tf 415 670 Td (Fecha: {esc(datos['fecha'])}  {esc(datos['hora'])}) Tj ET")

    # Datos del Médico
    ops.append("0.122 0.306 0.471 rg")
    ops.append("BT /F2 11 Tf 45 685 Td (DATOS DEL MEDICO) Tj ET")
    ops.append("0 0 0 rg")
    ops.append(f"BT /F1 10 Tf 45 670 Td (Doctor: {esc(datos['doctor'])}) Tj ET")
    ops.append(f"BT /F1 10 Tf 45 655 Td (Especialidad: {esc(datos['especialidad'])}) Tj ET")

    # Línea divisoria
    ops.append("0.75 0.75 0.75 RG 1 w 45 643 m 567 643 l S")

    # Datos del Paciente
    ops.append("0.122 0.306 0.471 rg")
    ops.append("BT /F2 11 Tf 45 625 Td (DATOS DEL PACIENTE) Tj ET")
    ops.append("0 0 0 rg")
    ops.append(f"BT /F1 10 Tf 45 610 Td (Paciente: {esc(datos['paciente'])}) Tj ET")
    ops.append(f"BT /F1 10 Tf 45 595 Td (Sexo: {esc(datos['sexo'])}    Fecha Nac.: {esc(datos['fecha_nac'])}) Tj ET")

    ops.append("0.75 0.75 0.75 RG 1 w 45 583 m 567 583 l S")

    # Diagnóstico / Historial
    y = 563
    ops.append("0.122 0.306 0.471 rg")
    ops.append(f"BT /F2 11 Tf 45 {y} Td (DIAGNOSTICO E HISTORIAL CLINICO) Tj ET")
    y -= 18
    ops.append("0 0 0 rg")
    for linea in envolver(datos["diagnostico"], 84):
        if y < 230:
            break
        ops.append(f"BT /F1 10 Tf 45 {y} Td ({esc(linea)}) Tj ET")
        y -= 14

    y -= 10
    ops.append("0.75 0.75 0.75 RG 1 w 45 " + str(y) + " m 567 " + str(y) + " l S")
    y -= 20

    # Prescripción / Medicamento
    ops.append("0.122 0.306 0.471 rg")
    ops.append(f"BT /F2 11 Tf 45 {y} Td (PRESCRIPCION MEDICA (Rp/)) Tj ET")
    y -= 18
    ops.append("0 0 0 rg")
    ops.append(f"BT /F2 10 Tf 45 {y} Td (Medicamento: {esc(datos['medicamento'])}) Tj ET")
    y -= 15
    ops.append(f"BT /F1 10 Tf 45 {y} Td (Presentacion: {esc(datos['presentacion'])}   |   Via: {esc(datos['via'])}) Tj ET")
    y -= 15
    ops.append(f"BT /F1 10 Tf 45 {y} Td (Duracion del tratamiento: {esc(datos['dias'])}) Tj ET")
    y -= 15
    ops.append(f"BT /F1 10 Tf 45 {y} Td (Horario de suministro: {esc(datos['horario'])}) Tj ET")

    # Firma del doctor al pie
    ops.append("0 0 0 RG 1 w 190 105 m 420 105 l S")
    ops.append(f"BT /F2 10 Tf 215 90 Td (Dr. {esc(datos['doctor'])}) Tj ET")
    ops.append("BT /F1 9 Tf 255 76 Td (Firma del Medico) Tj ET")

    stream = "\n".join(ops).encode("latin-1", errors="replace")

    objetos = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\nendobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n",
        (
            f"6 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objetos:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )

    with open(ruta_pdf, "wb") as f:
        f.write(pdf)


def _extraer_tratamiento(diagnostico):
    """Recupera días y horario si ya fueron guardados previamente en el texto del diagnóstico."""
    dias, horario = "", ""
    for linea in str(diagnostico).splitlines():
        if "Días:" in linea and "Horario:" in linea:
            partes = [p.strip() for p in linea.split("|")]
            for p in partes:
                if p.startswith("Días:"):
                    dias = p.replace("Días:", "").strip()
                elif p.startswith("Horario:"):
                    horario = p.replace("Horario:", "").strip()
    return dias, horario


# ======================================================================
# 1) REGISTRAR CONSULTA (SOLO DIAGNÓSTICO EN TEXTO)
# ======================================================================
def registrar_consulta(padre):
    citas = _opciones_citas()
    if citas is None:
        return
    if not citas:
        messagebox.showwarning("Sin citas", "No tienes citas registradas para realizar una consulta.")
        return

    win = tk.Toplevel(padre)
    win.title(f"Registrar Consulta - Usuario: {sesion.obtener()}")
    win.geometry("490x380")
    win.resizable(False, False)
    sesion.poner_saludo(win)

    tk.Label(
        win,
        text="REGISTRO DE DIAGNÓSTICO",
        font=("Arial", 10, "bold"),
        fg="#1f4e78",
    ).pack(pady=(6, 4))

    tk.Label(win, text="Cita a atender:").pack(pady=(4, 0))
    cb_cita = ttk.Combobox(win, values=citas, state="readonly", width=58)
    cb_cita.pack()

    tk.Label(win, text="Diagnóstico del paciente:").pack(pady=(10, 2))
    txt_diagnostico = tk.Text(win, width=54, height=9, wrap="word")
    txt_diagnostico.pack(padx=12)

    def guardar():
        if not cb_cita.get():
            messagebox.showwarning("Faltan datos", "Selecciona la cita correspondiente.", parent=win)
            return
        diagnostico = txt_diagnostico.get("1.0", tk.END).strip()
        if not diagnostico:
            messagebox.showwarning("Faltan datos", "Escribe el diagnóstico del paciente.", parent=win)
            return

        id_cita = _id_de(cb_cita.get())
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cur:
                cur.execute(
                    """INSERT INTO consulta (id_cita, diagnostico, id_medicamento)
                       VALUES (%s, %s, NULL) RETURNING id_consulta""",
                    (id_cita, diagnostico),
                )
                id_consulta = cur.fetchone()[0]
            conexion.commit()
            messagebox.showinfo(
                "Diagnóstico guardado",
                f"Diagnóstico registrado correctamente en el historial.\n\n"
                f"ID Consulta: {id_consulta}\n"
                f"Ahora puedes abrir 'Ver historial de consultas' para asignar medicamento y generar la receta.",
                parent=win,
            )
            cb_cita.set("")
            txt_diagnostico.delete("1.0", tk.END)
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al guardar diagnóstico", str(error), parent=win)

    tk.Button(win, text="Guardar diagnóstico", width=22, command=guardar).pack(pady=14)


# ======================================================================
# 2) HISTORIAL DE CONSULTAS: SELECCIONAR PACIENTE/DIAGNÓSTICO,
#    ASIGNAR MEDICAMENTO Y GENERAR RECETA PDF
# ======================================================================
def consultas_generales(padre):
    medicamentos = _opciones_medicamentos()
    if medicamentos is None:
        return

    win = tk.Toplevel(padre)
    win.title(f"Historial de Consultas - Usuario: {sesion.obtener()}")
    win.geometry("860x640")
    sesion.poner_saludo(win)

    tk.Label(
        win,
        text="1. Selecciona un paciente con su diagnóstico de la tabla:",
        font=("Arial", 10, "bold"),
        fg="#1f4e78",
    ).pack(anchor="w", padx=16, pady=(6, 4))

    # Tabla de consultas
    frame_tabla = tk.Frame(win)
    frame_tabla.pack(fill="both", expand=True, padx=16)

    columnas = ("id_consulta", "fecha", "hora", "paciente", "doctor", "medicamento", "diagnostico")
    tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=7, selectmode="browse")
    tree.heading("id_consulta", text="ID")
    tree.heading("fecha", text="Fecha")
    tree.heading("hora", text="Hora")
    tree.heading("paciente", text="Paciente")
    tree.heading("doctor", text="Doctor")
    tree.heading("medicamento", text="Medicamento")
    tree.heading("diagnostico", text="Diagnóstico")

    tree.column("id_consulta", width=45, anchor="center")
    tree.column("fecha", width=85, anchor="center")
    tree.column("hora", width=60, anchor="center")
    tree.column("paciente", width=165)
    tree.column("doctor", width=155)
    tree.column("medicamento", width=120)
    tree.column("diagnostico", width=200)

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    estado = {
        "registros": {},
        "id_consulta": None,
        "id_medicamento": None,
        "dias": "",
        "horario": "",
    }

    # Vista previa del diagnóstico seleccionado
    tk.Label(win, text="Diagnóstico / Historial del paciente seleccionado:", font=("Arial", 9, "bold")).pack(
        anchor="w", padx=16, pady=(8, 2)
    )
    txt_historial = tk.Text(win, height=5, wrap="word", state="disabled", bg="#f4f6f8")
    txt_historial.pack(fill="x", padx=16)

    lbl_seleccion = tk.Label(
        win,
        text="Ningún paciente seleccionado",
        font=("Arial", 9, "bold"),
        fg="#1f4e78",
    )
    lbl_seleccion.pack(anchor="w", padx=16, pady=(6, 2))

    ttk.Separator(win, orient="horizontal").pack(fill="x", padx=16, pady=6)

    # Sección para asignar medicamento, días y horario al paciente seleccionado
    tk.Label(
        win,
        text="2. Selecciona el medicamento, días del tratamiento y horario de suministro:",
        font=("Arial", 10, "bold"),
        fg="#1f4e78",
    ).pack(anchor="w", padx=16, pady=(2, 6))

    frame_form = tk.Frame(win)
    frame_form.pack(fill="x", padx=16)

    tk.Label(frame_form, text="Medicamento:").grid(row=0, column=0, sticky="w", pady=2)
    cb_med = ttk.Combobox(frame_form, values=medicamentos, state="readonly", width=48)
    cb_med.grid(row=0, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=2)

    tk.Label(frame_form, text="Días del tratamiento:").grid(row=1, column=0, sticky="w", pady=6)
    entry_dias = tk.Entry(frame_form, width=18)
    entry_dias.grid(row=1, column=1, sticky="w", padx=(8, 18), pady=6)

    tk.Label(frame_form, text="Horario de suministro:").grid(row=1, column=2, sticky="w", pady=6)
    cb_horario = ttk.Combobox(
        frame_form,
        values=[
            "Cada 4 horas",
            "Cada 6 horas",
            "Cada 8 horas",
            "Cada 12 horas",
            "Cada 24 horas",
            "Dosis única",
        ],
        width=20,
    )
    cb_horario.grid(row=1, column=3, sticky="w", padx=(8, 0), pady=6)

    def cargar_tabla(seleccionar_id=None):
        for item in tree.get_children():
            tree.delete(item)
        estado["registros"].clear()

        mpk = columna_pk("medicamento") or "id_medicamento"
        ppk = columna_pk("paciente") or "id_paciente"
        dpk = columna_pk("doctor") or "id_doctor"
        id_doc = sesion.obtener_id()

        sql = (
            "SELECT co.id_consulta, c.fecha, c.hora, p.nombre, d.nombre, "
            "co.id_medicamento, COALESCE(m.nombre, 'Sin asignar'), co.diagnostico "
            "FROM consulta co "
            "JOIN cita c ON c.id_cita = co.id_cita "
            f"JOIN paciente p ON p.{ppk} = c.id_paciente "
            f"JOIN doctor d ON d.{dpk} = c.id_doctor "
            f"LEFT JOIN medicamento m ON m.{mpk} = co.id_medicamento "
        )
        params = ()
        if id_doc is not None:
            sql += "WHERE c.id_doctor = %s "
            params = (id_doc,)
        sql += "ORDER BY co.id_consulta DESC"

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cur:
                cur.execute(sql, params)
                filas = cur.fetchall()
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error", f"No pude cargar el historial:\n{error}", parent=win)
            return

        item_a_seleccionar = None
        for fila in filas:
            cid, fecha, hora, pac, doc, id_med, nom_med, diag = fila
            estado["registros"][cid] = {
                "id_consulta": cid,
                "fecha": fecha.strftime("%d/%m/%Y"),
                "hora": hora.strftime("%H:%M"),
                "paciente": pac,
                "doctor": doc,
                "id_medicamento": id_med,
                "medicamento": nom_med,
                "diagnostico": diag,
            }
            resumen_diag = diag.splitlines()[0] if diag else ""
            iid = tree.insert(
                "",
                "end",
                values=(
                    cid,
                    fecha.strftime("%d/%m/%Y"),
                    hora.strftime("%H:%M"),
                    pac,
                    doc,
                    nom_med,
                    resumen_diag,
                ),
            )
            if seleccionar_id == cid:
                item_a_seleccionar = iid

        if item_a_seleccionar:
            tree.selection_set(item_a_seleccionar)
            tree.see(item_a_seleccionar)
            al_seleccionar()

    def al_seleccionar(_evento=None):
        sel = tree.selection()
        if not sel:
            return
        valores = tree.item(sel[0], "values")
        cid = int(valores[0])
        reg = estado["registros"].get(cid)
        if not reg:
            return

        estado["id_consulta"] = cid
        estado["id_medicamento"] = reg["id_medicamento"]

        lbl_seleccion.config(
            text=f"Seleccionado -> Consulta #{cid} | Paciente: {reg['paciente']} | Fecha: {reg['fecha']} {reg['hora']}"
        )

        txt_historial.config(state="normal")
        txt_historial.delete("1.0", tk.END)
        txt_historial.insert("1.0", reg["diagnostico"])
        txt_historial.config(state="disabled")

        # Si ya tenía un medicamento asignado, lo selecciona en el Combobox
        cb_med.set("")
        if reg["id_medicamento"] is not None:
            prefijo = f"{reg['id_medicamento']} - "
            for op in medicamentos:
                if op.startswith(prefijo):
                    cb_med.set(op)
                    break

        dias_prev, horario_prev = _extraer_tratamiento(reg["diagnostico"])
        estado["dias"] = dias_prev
        estado["horario"] = horario_prev
        entry_dias.delete(0, tk.END)
        if dias_prev:
            entry_dias.insert(0, dias_prev)
        cb_horario.set(horario_prev)

    tree.bind("<<TreeviewSelect>>", al_seleccionar)

    def guardar_medicamento():
        if estado["id_consulta"] is None:
            messagebox.showwarning(
                "Selecciona una consulta",
                "Primero haz clic en un paciente de la tabla superior.",
                parent=win,
            )
            return

        med_sel = cb_med.get()
        dias = entry_dias.get().strip()
        horario = cb_horario.get().strip()

        if not med_sel or not dias or not horario:
            messagebox.showwarning(
                "Faltan datos",
                "Selecciona el medicamento e indica los días del tratamiento y el horario de suministro.",
                parent=win,
            )
            return

        cid = estado["id_consulta"]
        reg = estado["registros"][cid]
        id_med = _id_de(med_sel)
        nombre_med = med_sel.split(" - ", 1)[1]
        dias_texto = f"{dias} días" if dias.isdigit() else dias

        # Conserva el diagnóstico base (antes de '--- Tratamiento ---') y actualiza el tratamiento
        diag_base = reg["diagnostico"].split("\n--- Tratamiento ---\n")[0].strip()
        historial_completo = (
            f"{diag_base}\n"
            f"--- Tratamiento ---\n"
            f"Medicamento: {nombre_med} | Días: {dias_texto} | Horario: {horario}"
        )

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cur:
                cur.execute(
                    """UPDATE consulta
                       SET id_medicamento = %s, diagnostico = %s
                       WHERE id_consulta = %s""",
                    (id_med, historial_completo, cid),
                )
            conexion.commit()
            messagebox.showinfo(
                "Medicamento guardado",
                "Medicamento, días de tratamiento y horario registrados en el historial del paciente.",
                parent=win,
            )
            cargar_tabla(seleccionar_id=cid)
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al guardar medicamento", str(error), parent=win)

    def generar_receta():
        if estado["id_consulta"] is None:
            messagebox.showwarning(
                "Selecciona una consulta",
                "Primero selecciona al paciente con su diagnóstico en la tabla.",
                parent=win,
            )
            return

        cid = estado["id_consulta"]
        reg = estado["registros"][cid]

        if reg["id_medicamento"] is None:
            messagebox.showwarning(
                "Falta medicamento",
                "Primero selecciona el medicamento, días y horario y presiona 'Guardar medicamento en historial'.",
                parent=win,
            )
            return

        ppk = columna_pk("paciente") or "id_paciente"
        dpk = columna_pk("doctor") or "id_doctor"
        mpk = columna_pk("medicamento") or "id_medicamento"
        conexion = obtener_conexion()

        try:
            with conexion.cursor() as cur:
                cur.execute(
                    "SELECT co.id_consulta, co.diagnostico, "
                    "c.fecha, c.hora, "
                    "p.nombre, COALESCE(p.sexo, 'N/A'), COALESCE(p.fecha_nac::text, 'N/A'), "
                    "d.nombre, COALESCE(d.especialidad, 'Medicina General'), "
                    "m.nombre, m.presentacion, m.via_administracion "
                    "FROM consulta co "
                    "JOIN cita c ON c.id_cita = co.id_cita "
                    f"JOIN paciente p ON p.{ppk} = c.id_paciente "
                    f"JOIN doctor d ON d.{dpk} = c.id_doctor "
                    f"JOIN medicamento m ON m.{mpk} = co.id_medicamento "
                    "WHERE co.id_consulta = %s",
                    (cid,),
                )
                fila = cur.fetchone()
        except Exception as error:
            conexion.rollback()
            messagebox.showerror("Error al consultar datos de la receta", str(error), parent=win)
            return

        if not fila:
            messagebox.showerror("Error", "No se encontraron los datos completos de la consulta.", parent=win)
            return

        dias_final = estado["dias"] or entry_dias.get().strip() or "Según indicación médica"
        horario_final = estado["horario"] or cb_horario.get().strip() or "Según indicación médica"

        datos_receta = {
            "id_consulta": fila[0],
            "diagnostico": fila[1],
            "fecha": fila[2].strftime("%d/%m/%Y"),
            "hora": fila[3].strftime("%H:%M"),
            "paciente": fila[4],
            "sexo": fila[5],
            "fecha_nac": fila[6],
            "doctor": fila[7],
            "especialidad": fila[8],
            "medicamento": fila[9],
            "presentacion": fila[10],
            "via": fila[11],
            "dias": dias_final,
            "horario": horario_final,
        }

        ruta_pdf = os.path.abspath("receta.pdf")
        try:
            _crear_pdf_receta(ruta_pdf, datos_receta)
        except Exception as error:
            messagebox.showerror("Error al crear receta.pdf", str(error), parent=win)
            return

        messagebox.showinfo(
            "Receta generada",
            f"Se generó correctamente el archivo:\n{ruta_pdf}",
            parent=win,
        )

        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta_pdf)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta_pdf])
            else:
                subprocess.Popen(["xdg-open", ruta_pdf])
        except Exception:
            pass

    # Botones de acción al pie
    frame_botones = tk.Frame(win)
    frame_botones.pack(pady=14)

    tk.Button(
        frame_botones,
        text="Guardar medicamento en historial",
        width=28,
        command=guardar_medicamento,
    ).pack(side="left", padx=10)

    tk.Button(
        frame_botones,
        text="GENERAR RECETA",
        width=22,
        bg="#1f4e78",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2",
        command=generar_receta,
    ).pack(side="left", padx=10)

    cargar_tabla()