from src.estructuras.cola import Cola
from src.estructuras.lista_simple import ListaSimple
from src.estructuras.pila import Pila


class NodoArbol:
    """Un día: su fecha, la lista de gastos de ese día y sus dos hijos."""

    def __init__(self, fecha):
        self.fecha = fecha
        self.gastos = ListaSimple()
        self.izquierdo = None
        self.derecho = None


class ArbolFechas:
    """Árbol binario de búsqueda (BST) por fecha. Un nodo = un día."""
    def __init__(self):
        """O(1)."""
        self._raiz = None
        self._tamano = 0

    # ---------- Inserción ----------

    def insertar(self, gasto):
        """Agrega el gasto al nodo de su fecha; crea el nodo si no existe.
        O(h) para llegar al día más O(1) para insertar en su lista."""
        nodo = self._nodo_del_dia(gasto.fecha)
        nodo.gastos.insertar(gasto)
        self._tamano += 1

    def _nodo_del_dia(self, fecha):
        """Devuelve el nodo de esa fecha, creándolo si hace falta. O(h)."""
        if self._raiz is None:
            self._raiz = NodoArbol(fecha)
            return self._raiz
        actual = self._raiz
        while True:
            if fecha == actual.fecha:
                return actual
            if fecha < actual.fecha:
                if actual.izquierdo is None:
                    actual.izquierdo = NodoArbol(fecha)
                    return actual.izquierdo
                actual = actual.izquierdo
            else:
                if actual.derecho is None:
                    actual.derecho = NodoArbol(fecha)
                    return actual.derecho
                actual = actual.derecho

    # ---------- Consultas ----------

    def buscar_dia(self, fecha):
        """Devuelve la ListaSimple del día, o None si no hay gastos. O(h)."""
        nodo = self._buscar_nodo(fecha)
        return None if nodo is None else nodo.gastos

    def _buscar_nodo(self, fecha):
        """Nodo de esa fecha, o None. Iterativo, sin recursión. O(h)."""
        actual = self._raiz
        while actual is not None:
            if fecha == actual.fecha:
                return actual
            actual = actual.izquierdo if fecha < actual.fecha else actual.derecho
        return None

    def en_orden(self):
        """Todos los gastos, de la fecha más antigua a la más reciente.
        Recorrido en orden con una Pila propia en vez de recursión.
        O(n) en días más los gastos que se recorren."""
        pila = Pila()
        actual = self._raiz
        while actual is not None or not pila.esta_vacia():
            while actual is not None:
                pila.apilar(actual)
                actual = actual.izquierdo
            actual = pila.desapilar()
            yield from actual.gastos
            actual = actual.derecho

    def consultar_rango(self, desde, hasta):
        """Gastos con desde <= fecha <= hasta, en orden de fecha.

        Igual que en_orden, pero solo baja por la izquierda si puede haber
        fechas >= desde y se detiene al pasar de hasta: descarta las ramas
        fuera del rango. O(h + k) con k los gastos devueltos. Si
        desde > hasta, no devuelve nada."""
        pila = Pila()
        actual = self._raiz
        while actual is not None or not pila.esta_vacia():
            while actual is not None:
                pila.apilar(actual)
                actual = actual.izquierdo if desde < actual.fecha else None
            actual = pila.desapilar()
            if actual.fecha > hasta:
                return
            if actual.fecha >= desde:
                yield from actual.gastos
            actual = actual.derecho

    def total_rango(self, desde, hasta):
        """Suma de montos (entero, COP) en el rango inclusivo. O(h + k)."""
        total = 0
        for gasto in self.consultar_rango(desde, hasta):
            total += gasto.monto
        return total

    # ---------- Borrado ----------

    def eliminar(self, fecha, id_gasto):
        """Quita el gasto de ese día y lo devuelve; None si no existe.

        Si el día queda sin gastos, se borra su nodo del árbol (0, 1 o 2
        hijos). O(h + m), con m los gastos de ese día."""
        nodo = self._buscar_nodo(fecha)
        if nodo is None:
            return None
        gasto = nodo.gastos.eliminar(id_gasto)
        if gasto is None:
            return None
        self._tamano -= 1
        if nodo.gastos.esta_vacia():
            self._quitar_nodo(fecha)
        return gasto

    def _quitar_nodo(self, fecha):
        """Quita del árbol el nodo de esa fecha (que debe existir). Iterativo.
        Con dos hijos, lo reemplaza el sucesor en orden (el menor del
        subárbol derecho). O(h)."""
        padre = None
        nodo = self._raiz
        while nodo.fecha != fecha:
            padre = nodo
            nodo = nodo.izquierdo if fecha < nodo.fecha else nodo.derecho
        if nodo.izquierdo is not None and nodo.derecho is not None:
            padre, sucesor = nodo, nodo.derecho
            while sucesor.izquierdo is not None:
                padre, sucesor = sucesor, sucesor.izquierdo
            nodo.fecha = sucesor.fecha
            nodo.gastos = sucesor.gastos
            nodo = sucesor
        hijo = nodo.izquierdo if nodo.izquierdo is not None else nodo.derecho
        self._reenlazar(padre, nodo, hijo)

    def _reenlazar(self, padre, viejo, nuevo):
        """Pone `nuevo` donde estaba `viejo` bajo `padre` (None = raíz)."""
        if padre is None:
            self._raiz = nuevo
        elif padre.izquierdo is viejo:
            padre.izquierdo = nuevo
        else:
            padre.derecho = nuevo

    # ---------- Tamaño ----------

    def __len__(self):
        """Cantidad de gastos. O(1) porque se lleva un contador."""
        return self._tamano

    def esta_vacio(self):
        """True si no hay gastos. O(1)."""
        return self._raiz is None

    def altura(self):
        """Niveles del árbol (vacío = 0), recorriendo por niveles con una
        Cola propia. Sirve para mostrar la degeneración. O(n)."""
        cola = Cola()
        if self._raiz is not None:
            cola.encolar(self._raiz)
        niveles = 0
        while not cola.esta_vacia():
            niveles += 1
            for _ in range(len(cola)):
                nodo = cola.desencolar()
                for hijo in (nodo.izquierdo, nodo.derecho):
                    if hijo is not None:
                        cola.encolar(hijo)
        return niveles
