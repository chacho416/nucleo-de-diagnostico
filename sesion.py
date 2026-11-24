"""Guarda quién tiene la sesión iniciada y muestra el saludo en cualquier ventana."""
import tkinter as tk

_nombre = ""


def iniciar(nombre):
    global _nombre
    _nombre = nombre


def cerrar():
    global _nombre
    _nombre = ""


def obtener():
    return _nombre


def poner_saludo(ventana):
    """Coloca 'Hola, NOMBRE' en la parte superior derecha de la ventana.
    Debe llamarse antes de agregar los demás elementos."""
    tk.Label(ventana, text=f"Hola, {_nombre}", font=("Arial", 11, "bold")).pack(
        anchor="ne", padx=12, pady=6)