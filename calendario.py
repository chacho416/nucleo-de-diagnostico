"""Selectores interactivos de fecha (calendario) y hora, hechos solo con Tkinter."""
import calendar
import datetime
import tkinter as tk
from tkinter import ttk

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
AZUL = "#1f4e78"
TODOS_LOS_MINUTOS = tuple(f"{m:02d}" for m in range(60))   # 00, 01, 02 ... 59


class SelectorFecha(tk.Frame):
    """Campo de fecha con un calendario desplegable. Los días pasados no se pueden elegir."""

    def __init__(self, padre, fecha_minima=None):
        super().__init__(padre)
        self._fecha = None
        self._minima = fecha_minima or datetime.date.today()
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
        tk.Button(encabezado, text="<", width=3, command=lambda: mover(-1)).pack(side=tk.LEFT, padx=6)
        titulo = tk.Label(encabezado, font=("Arial", 11, "bold"), fg=AZUL)
        titulo.pack(side=tk.LEFT, expand=True)
        tk.Button(encabezado, text=">", width=3, command=lambda: mover(1)).pack(side=tk.RIGHT, padx=6)

        cuerpo = tk.Frame(top)
        cuerpo.pack(padx=8, pady=(0, 8))

        def elegir(dia):
            self.set(datetime.date(estado["anio"], estado["mes"], dia))
            top.destroy()

        def dibujar():
            for w in cuerpo.winfo_children():
                w.destroy()
            anio, mes = estado["anio"], estado["mes"]
            titulo.config(text=f"{MESES[mes - 1]} {anio}")
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
            estado["anio"] += (mes - 1) // 12
            estado["mes"] = (mes - 1) % 12 + 1
            dibujar()

        dibujar()
        top.grab_set()


class SelectorHora(tk.Frame):
    """Campo de hora con listas de hora y minutos (todos los minutos, de 00 a 59).
    Las horas van de hora_inicio hasta hora_fin - 1.
    Con ultima_hora_solo_en_punto=True, en la última hora solo se puede elegir :00."""

    def __init__(self, padre, hora_inicio=9, hora_fin=20, minutos=TODOS_LOS_MINUTOS,
                 ultima_hora_solo_en_punto=False):
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
        tk.Label(self, text="hrs").pack(side=tk.LEFT, padx=(6, 0))

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

    def set(self, hora):
        """Pone una hora (datetime.time) en los selectores."""
        self._hora.set(f"{hora.hour:02d}")
        self._min.config(values=self._minutos)
        self._min.set(f"{hora.minute:02d}")

    def clear(self):
        self._hora.set("")
        self._min.config(values=self._minutos)
        self._min.set("00")