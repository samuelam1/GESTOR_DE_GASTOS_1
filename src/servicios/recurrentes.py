from datetime import date

from src.estructuras.cola import Cola
from src.modelos.categoria import clave_comparacion
from src.modelos.recurrente import Recurrente
from src.modelos.validaciones import validar_fecha, validar_id
from src.servicios.meses import limites_del_mes


class ServicioRecurrentes:
    """Obligaciones mensuales y la cola de pendientes del mes.

    No generan gastos solos: el gasto se crea únicamente al pagar. La cola
    se reconstruye desde la lista de recurrentes cada vez que se consulta,
    así siempre refleja los pagos, borrados y deshacer recientes (O(r + k)).
    """

    def __init__(self, servicio_gastos, reloj=date.today):
        self._gastos = servicio_gastos
        self._reloj = reloj
        self._recurrentes = []
        self._siguiente_id = 1
        self._cola = Cola()

    # ---------- Alta, listado, terminar ----------

    def agregar(self, monto, categoria, descripcion, dia, nota=""):
        """Crea un recurrente activo con id nuevo. O(c)."""
        recurrente = Recurrente(
            id=self._siguiente_id,
            monto=monto,
            categoria=self._gastos.resolver_categoria(categoria),
            descripcion=descripcion,
            dia=dia,
            nota=nota,
        )
        self._siguiente_id += 1
        self._recurrentes.append(recurrente)
        return recurrente

    def listar(self):
        """Todos, activos e inactivos. O(r)."""
        return list(self._recurrentes)

    def listar_activos(self):
        """O(r)."""
        return [r for r in self._recurrentes if r.activo]

    def buscar(self, id_recurrente):
        """El recurrente con ese id, o None. O(r)."""
        for recurrente in self._recurrentes:
            if recurrente.id == id_recurrente:
                return recurrente
        return None

    def _exigir(self, id_recurrente):
        validar_id(id_recurrente, "El id del recurrente")
        recurrente = self.buscar(id_recurrente)
        if recurrente is None:
            raise ValueError(f"No existe el recurrente {id_recurrente}")
        return recurrente

    def terminar(self, id_recurrente):
        """Lo deja inactivo (no se borra). O(r)."""
        recurrente = self._exigir(id_recurrente)
        recurrente.terminar()
        return recurrente

    # ---------- Pendientes del mes ----------

    def esta_pagado(self, id_recurrente, anio, mes):
        """True si hay un gasto con ese recurrente_id en el mes. O(h + k)."""
        primero, ultimo = limites_del_mes(anio, mes)
        for gasto in self._gastos.consultar_rango(primero, ultimo):
            if gasto.recurrente_id == id_recurrente:
                return True
        return False

    def reconstruir_cola(self):
        """Encola los activos sin pago en el mes actual, ordenados por su
        fecha de vencimiento (el día 31 en un mes corto cuenta como el
        último día). Solo el mes actual: lo no pagado de meses anteriores
        no se arrastra. O(r log r + r (h + k))."""
        hoy = self._reloj()
        pendientes = [
            r for r in self._recurrentes
            if r.activo and not self.esta_pagado(r.id, hoy.year, hoy.month)
        ]
        pendientes.sort(key=lambda r: (r.fecha_en(hoy.year, hoy.month), r.id))
        self._cola.vaciar()
        for recurrente in pendientes:
            self._cola.encolar(recurrente)
        return self._cola

    def pendientes(self):
        """Pendientes del mes en orden de día. O(r (h + k))."""
        return list(self.reconstruir_cola())

    def proximo_pendiente(self):
        """El que vence primero, o None si no hay. O(r (h + k))."""
        cola = self.reconstruir_cola()
        return None if cola.esta_vacia() else cola.ver_frente()

    # ---------- Pagar ----------

    def pagar(self, id_recurrente, monto=None, fecha=None):
        """Registra el gasto del recurrente. Por defecto usa el monto de la
        plantilla y la fecha de hoy. No se puede pagar dos veces en un mismo
        mes ni un recurrente terminado. O(r + h + k)."""
        recurrente = self._exigir(id_recurrente)
        if not recurrente.activo:
            raise ValueError("El recurrente está terminado y no se puede pagar")
        dia_pago = self._reloj() if fecha is None else validar_fecha(fecha)
        if self.esta_pagado(recurrente.id, dia_pago.year, dia_pago.month):
            raise ValueError("Ese recurrente ya está pagado en ese mes")
        gasto = self._gastos.registrar(
            monto=recurrente.monto if monto is None else monto,
            fecha=dia_pago,
            categoria=recurrente.categoria,
            descripcion=recurrente.descripcion,
            origen="recurrente",
            recurrente_id=recurrente.id,
        )
        self.reconstruir_cola()
        return gasto

    # ---------- Categorías y persistencia ----------

    def reasignar_categoria(self, origen, destino):
        """Los recurrentes de una categoría eliminada pasan a 'Otros'. O(r)."""
        clave = clave_comparacion(origen)
        for recurrente in self._recurrentes:
            if clave_comparacion(recurrente.categoria) == clave:
                recurrente.categoria = destino

    def siguiente_id(self):
        return self._siguiente_id

    def cargar(self, recurrentes, siguiente_id):
        """Reemplaza el estado con datos ya validados. O(r)."""
        self._recurrentes = list(recurrentes)
        self._siguiente_id = siguiente_id
        self._cola.vaciar()
