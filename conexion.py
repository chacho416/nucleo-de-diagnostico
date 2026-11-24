"""Manejo de la conexión a PostgreSQL (se comparte con todos los módulos)."""
import psycopg
from tkinter import messagebox

_conexion = None


def conectar(usuario, contrasena):
    try:
        conexion = psycopg.connect(
            host="localhost",
            port="5432",
            dbname="nucleo_de_diagnostico",
            user="admin",
            password="1234",
        )
        print("Conexión exitosa")
        return conexion

    except Exception as error:
        print("Error real:", error)
        messagebox.showerror("Detalle del error", str(error))
        return None


def guardar_conexion(conexion):
    global _conexion
    _conexion = conexion


def obtener_conexion():
    return _conexion


def cerrar_conexion():
    global _conexion
    if _conexion:
        _conexion.close()
        _conexion = None