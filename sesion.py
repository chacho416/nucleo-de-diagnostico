"""Guarda los datos del usuario que inició sesión."""
import tkinter as tk

_usuario = None
_id_usuario = None


def iniciar(nombre, id_usuario=None):
    global _usuario, _id_usuario
    _usuario = nombre
    _id_usuario = id_usuario


def obtener():
    return _usuario or ""


def obtener_id():
    return _id_usuario


def cerrar():
    global _usuario, _id_usuario
    _usuario = None
    _id_usuario = None


def poner_saludo(ventana):
    tk.Label(
        ventana,
        text=f"Usuario: {obtener()}",
        font=("Arial", 9, "bold"),
        fg="#1f4e78"
    ).pack(pady=(6, 2))