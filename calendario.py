"""Selectores interactivos de fecha (calendario) y hora, hechos solo con Tkinter."""
import calendar
import datetime
import tkinter as tk
from tkinter import ttk

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
AZUL = "#1f4e78"
ANIO_MIN, ANIO_MAX = 1900, 2200
TODOS_LOS_MINUTOS = tuple(f"{m:02d}" for m in range(60))


class SelectorFecha(tk.Frame):
    """Campo de fecha con un calendario desplegable. Permite elegir cualquier día del año."""

    def __init__(self, padre, fecha_minima=None):
        super().__init__(padre)
        self._fecha = None
        self._minima = fecha_minima or datetime.date.min
        self._var = tk.StringVar()
        tk.Entry(self, textvariable=self._var, width=14, state="readonly",
                 justify="center").pack(side=tk.LEFT)
        tk.Button(self, text="Calendario", command=self._abrir).pack(side=tk.LEFT, padx=(6, 0))

    def get(self):
        """Devuelve la fecha elegida (datetime.date) o None."""
        return self._fecha

    def set(self, fecha):
        self._fecha = fecha
        self._var.set(fecha.strftime("%d/%m/%Y") if fecha else "")

    def clear(self):
        self.set(None)

    def _abrir(self):
        base = self._fecha or datetime.date.today()
        estado = {"anio": base.year, "mes": base.month}

        top = tk.Toplevel(self)
        top.title("Elige la fecha")
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.geometry(f"+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 4}")

        encabezado = tk.Frame(top)
        encabezado.pack(fill=tk.X, pady=6)

        btn_anterior = tk.Button(encabezado, text="<", width=3)
        btn_anterior.pack(side=tk.LEFT, padx=6)

        centro = tk.Frame(encabezado)
        centro.pack(side=tk.LEFT, expand=True)
        cb_mes = ttk.Combobox(centro, values=MESES, state="readonly", width=11)
        cb_mes.pack(side=tk.LEFT, padx=(0, 6))
        var_anio = tk.StringVar()
        sp_anio = ttk.Spinbox(centro, from_=ANIO_MIN, to=ANIO_MAX, width=6,
                              textvariable=var_anio)
        sp_anio.pack(side=tk.LEFT)

        btn_siguiente = tk.Button(encabezado, text=">", width=3)
        btn_siguiente.pack(side=tk.RIGHT, padx=6)

        cuerpo = tk.Frame(top)
        cuerpo.pack(padx=8, pady=(0, 8))

        def elegir(dia):
            self.set(datetime.date(estado["anio"], estado["mes"], dia))
            top.destroy()

        def dibujar():
            for w in cuerpo.winfo_children():
                w.destroy()
            anio, mes = estado["anio"], estado["mes"]
            cb_mes.current(mes - 1)
            var_anio.set(str(anio))
            for c, nombre in enumerate(DIAS):
                tk.Label(cuerpo, text=nombre, width=4, fg=AZUL,
                         font=("Arial", 9, "bold")).grid(row=0, column=c)
            hoy = datetime.date.today()
            for fila, semana in enumerate(calendar.monthcalendar(anio, mes), start=1):
                for c, dia in enumerate(semana):
                    if dia == 0:
                        continue
                    fecha = datetime.date(anio, mes, dia)
                    boton = tk.Button(cuerpo, text=str(dia), width=4,
                                      command=lambda d=dia: elegir(d))
                    if fecha < self._minima:
                        boton.config(state=tk.DISABLED)
                    elif fecha == self._fecha:
                        boton.config(bg=AZUL, fg="white")
                    elif fecha == hoy:
                        boton.config(bg="#cfe8ff")
                    boton.grid(row=fila, column=c, padx=1, pady=1)

        def mover(delta):
            mes = estado["mes"] + delta
            nuevo_anio = estado["anio"] + (mes - 1) // 12
            nuevo_mes = (mes - 1) % 12 + 1
            if ANIO_MIN <= nuevo_anio <= ANIO_MAX:
                estado["anio"] = nuevo_anio
                estado["mes"] = nuevo_mes
                dibujar()

        def ir_a_seleccion(_evento=None):
            try:
                anio = int(var_anio.get())
            except ValueError:
                var_anio.set(str(estado["anio"]))
                return
            estado["anio"] = min(max(anio, ANIO_MIN), ANIO_MAX)
            estado["mes"] = cb_mes.current() + 1
            dibujar()

        btn_anterior.config(command=lambda: mover(-1))
        btn_siguiente.config(command=lambda: mover(1))
        sp_anio.config(command=ir_a_seleccion)
        cb_mes.bind("<<ComboboxSelected>>", ir_a_seleccion)
        sp_anio.bind("<Return>", ir_a_seleccion)
        sp_anio.bind("<FocusOut>", ir_a_seleccion)

        dibujar()
        top.grab_set()


class SelectorHora(tk.Frame):
    """Campo de hora en formato de 24 horas (09:00 a 20:00)."""

    def __init__(self, padre, hora_inicio=9, hora_fin=21, minutos=("00", "15", "30", "45"),
                 ultima_hora_solo_en_punto=True):
        super().__init__(padre)
        self._solo_en_punto = ultima_hora_solo_en_punto
        self._minutos = list(minutos)
        self._hora_limite = hora_fin - 1
        horas = [f"{h:02d}" for h in range(hora_inicio, hora_fin)]
        self._hora = ttk.Combobox(self, values=horas, width=4, state="readonly", justify="center")
        self._min = ttk.Combobox(self, values=self._minutos, width=4, state="readonly",
                                 justify="center")
        self._min.set("00")
        self._hora.bind("<<ComboboxSelected>>", self._ajustar_minutos)
        self._hora.pack(side=tk.LEFT)
        tk.Label(self, text=":", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=3)
        self._min.pack(side=tk.LEFT)
        tk.Label(self, text="hrs (24h)").pack(side=tk.LEFT, padx=(6, 0))

    def _ajustar_minutos(self, _event=None):
        if self._solo_en_punto and self._hora.get() == f"{self._hora_limite:02d}":
            self._min.config(values=["00"])
            self._min.set("00")
        else:
            self._min.config(values=self._minutos)

    def set(self, hora):
        """Pone una hora (datetime.time) en el selector."""
        self._hora.set(f"{hora.hour:02d}")
        self._ajustar_minutos()
        self._min.set(f"{hora.minute:02d}")

    def get(self):
        """Devuelve la hora elegida (datetime.time) o None si no se eligió la hora."""
        if not self._hora.get():
            return None
        return datetime.time(int(self._hora.get()), int(self._min.get() or 0))

    def clear(self):
        self._hora.set("")
        self._min.config(values=self._minutos)
        self._min.set("00")