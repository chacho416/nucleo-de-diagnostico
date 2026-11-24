"""Módulo de EMPLEADOS (Paso 4)."""
from tabla import mostrar_tabla

TABLA_EMPLEADAS = "empleado"


def consultas_generales(padre):
    mostrar_tabla(padre, "Consultas generales - Empleadas", TABLA_EMPLEADAS)