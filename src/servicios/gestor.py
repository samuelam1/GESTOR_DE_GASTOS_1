from datetime import date

from src.modelos.categoria import CATEGORIA_OTROS
from src.servicios.gastos import ServicioGastos
from src.servicios.recurrentes import ServicioRecurrentes


class Gestor:
    """Punto de entrada para la interfaz: junta gastos y recurrentes.

    `reloj` es una función que devuelve la fecha de hoy; se inyecta para
    poder probar con fechas fijas.
    """

    def __init__(self, reloj=date.today):
        self.reloj = reloj
        self.gastos = ServicioGastos(reloj)
        self.recurrentes = ServicioRecurrentes(self.gastos, reloj)

    def eliminar_categoria(self, nombre):
        """Quita la categoría; sus gastos y recurrentes pasan a 'Otros'.
        'Otros' y las de por defecto no se eliminan. Devuelve cuántos gastos
        se movieron. No se puede deshacer. O(n + r)."""
        canonico = self.gastos.quitar_categoria(nombre)
        movidos = self.gastos.reasignar_categoria(canonico, CATEGORIA_OTROS)
        self.recurrentes.reasignar_categoria(canonico, CATEGORIA_OTROS)
        return movidos

    def deshacer(self):
        """Deshace la última operación sobre gastos y reconstruye pendientes.
        Devuelve (operación, gasto) o None. O(n + r (h + k))."""
        resultado = self.gastos.deshacer()
        self.recurrentes.reconstruir_cola()
        return resultado

    def borrar_gasto(self, id_gasto):
        """Borra un gasto; si era de un recurrente, vuelve a pendiente."""
        gasto = self.gastos.borrar(id_gasto)
        self.recurrentes.reconstruir_cola()
        return gasto
