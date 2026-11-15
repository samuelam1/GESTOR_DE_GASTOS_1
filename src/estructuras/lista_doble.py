class NodoDoble:
    """Un eslabón con enlace al anterior y al siguiente."""

    def __init__(self, valor):
        self.valor = valor
        self.anterior = None
        self.siguiente = None


class ListaDoble:
    """Lista doblemente enlazada ordenada, con un cursor (la posición actual).

    Se usa para navegar entre meses ("AAAA-MM"; el orden de texto coincide
    con el cronológico). Los valores se comparan con < y ==.

    Contrato:
    - insertar_ordenado no admite repetidos (devuelve False si ya estaba).
    - El cursor queda en el primer valor insertado y no se mueve al insertar.
    - mover_anterior / mover_siguiente devuelven False en los extremos.
    - No usa list, dict ni deque de Python.
    """

    def __init__(self):
        """O(1)."""
        self._cabeza = None
        self._cola = None
        self._actual = None
        self._tamano = 0

    def insertar_ordenado(self, valor):
        """Inserta en su lugar. Devuelve False si ya existía. O(n)."""
        posterior = self._cabeza
        while posterior is not None and posterior.valor < valor:
            posterior = posterior.siguiente
        if posterior is not None and posterior.valor == valor:
            return False
        self._enlazar_antes_de(valor, posterior)
        return True

    def _enlazar_antes_de(self, valor, posterior):
        """Crea el nodo y lo pone antes de `posterior` (None = al final)."""
        nodo = NodoDoble(valor)
        nodo.siguiente = posterior
        nodo.anterior = self._cola if posterior is None else posterior.anterior
        if nodo.anterior is None:
            self._cabeza = nodo
        else:
            nodo.anterior.siguiente = nodo
        if posterior is None:
            self._cola = nodo
        else:
            posterior.anterior = nodo
        if self._actual is None:
            self._actual = nodo
        self._tamano += 1

    def _buscar_nodo(self, valor):
        actual = self._cabeza
        while actual is not None:
            if actual.valor == valor:
                return actual
            actual = actual.siguiente
        return None

    def contiene(self, valor):
        """O(n)."""
        return self._buscar_nodo(valor) is not None

    def eliminar(self, valor):
        """Quita el valor; devuelve False si no estaba. Si el cursor
        estaba ahí, pasa al siguiente (o al anterior si era el último). O(n)."""
        nodo = self._buscar_nodo(valor)
        if nodo is None:
            return False
        if self._actual is nodo:
            self._actual = nodo.siguiente or nodo.anterior
        if nodo.anterior is None:
            self._cabeza = nodo.siguiente
        else:
            nodo.anterior.siguiente = nodo.siguiente
        if nodo.siguiente is None:
            self._cola = nodo.anterior
        else:
            nodo.siguiente.anterior = nodo.anterior
        self._tamano -= 1
        return True

    # ---------- Cursor ----------

    @property
    def actual(self):
        """Valor bajo el cursor, o None si la lista está vacía. O(1)."""
        return None if self._actual is None else self._actual.valor

    def ir_a(self, valor):
        """Pone el cursor en el valor; False si no existe. O(n)."""
        nodo = self._buscar_nodo(valor)
        if nodo is None:
            return False
        self._actual = nodo
        return True

    def hay_anterior(self):
        """O(1)."""
        return self._actual is not None and self._actual.anterior is not None

    def hay_siguiente(self):
        """O(1)."""
        return self._actual is not None and self._actual.siguiente is not None

    def mover_anterior(self):
        """Retrocede el cursor; False si ya está en el primero. O(1)."""
        if not self.hay_anterior():
            return False
        self._actual = self._actual.anterior
        return True

    def mover_siguiente(self):
        """Avanza el cursor; False si ya está en el último. O(1)."""
        if not self.hay_siguiente():
            return False
        self._actual = self._actual.siguiente
        return True

    # ---------- Tamaño y recorridos ----------

    def esta_vacia(self):
        """O(1)."""
        return self._cabeza is None

    def __len__(self):
        """O(1) con contador."""
        return self._tamano

    def __iter__(self):
        """Del primero al último. O(n)."""
        actual = self._cabeza
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def __reversed__(self):
        """Del último al primero, usando los enlaces anteriores. O(n)."""
        actual = self._cola
        while actual is not None:
            yield actual.valor
            actual = actual.anterior


