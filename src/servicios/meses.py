import calendar
from datetime import date

from src.estructuras.lista_doble import ListaDoble


def mes_de(fecha):
    """Texto 'AAAA-MM' de una fecha. O(1)."""
    return f"{fecha.year:04d}-{fecha.month:02d}"


def partir_mes(mes):
    """('AAAA-MM') -> (anio, mes) como enteros. O(1)."""
    anio, numero = mes.split("-")
    return int(anio), int(numero)


def limites_del_mes(anio, mes):
    """Primer y último día del mes como fechas. O(1)."""
    ultimo = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, 1), date(anio, mes, ultimo)


class NavegadorMeses:
    """Navega entre meses con una lista doble. No guarda totales: los pide
    al servicio de gastos (consulta por rango del árbol), para no tener dos
    fuentes de verdad."""

    def __init__(self, servicio, mes_inicial):
        """O(1)."""
        self._servicio = servicio
        self._meses = ListaDoble()
        self._meses.insertar_ordenado(mes_inicial)

    def registrar_mes(self, mes):
        """Agrega el mes si no estaba (el cursor no se mueve). O(m)."""
        self._meses.insertar_ordenado(mes)

    def mes_actual(self):
        """O(1)."""
        return self._meses.actual

    def hay_anterior(self):
        return self._meses.hay_anterior()

    def hay_siguiente(self):
        return self._meses.hay_siguiente()

    def anterior(self):
        """Retrocede un mes; False si ya es el primero. O(1)."""
        return self._meses.mover_anterior()

    def siguiente(self):
        """Avanza un mes; False si ya es el último. O(1)."""
        return self._meses.mover_siguiente()

    def ir_a(self, mes):
        """Salta a un mes que esté en la lista; False si no. O(m)."""
        return self._meses.ir_a(mes)

    def meses(self):
        """Todos los meses conocidos, en orden. O(m)."""
        return list(self._meses)

    def total_actual(self):
        """Total del mes bajo el cursor, por consulta de rango. O(h + k)."""
        anio, mes = partir_mes(self.mes_actual())
        return self._servicio.total_mes(anio, mes)

    def gastos_actual(self):
        """Gastos del mes bajo el cursor, en orden de fecha. O(h + k)."""
        anio, mes = partir_mes(self.mes_actual())
        return self._servicio.gastos_del_mes(anio, mes)
