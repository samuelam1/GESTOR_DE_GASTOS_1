class NodoPila:
    """Un elemento de la pila y el que tiene debajo (o None)."""

    def __init__(self, valor):
        self.valor = valor
        self.debajo = None


class Pila:
    
    """Pila (LIFO) enlazada. Se usa para deshacer operaciones.
    - desapilar y ver_tope en una pila vacía lanzan IndexError.
    """

    def __init__(self):
        """O(1)."""
        self._tope = None
        self._tamano = 0

    def apilar(self, valor):
        """Pone el valor encima. O(1)."""
        nodo = NodoPila(valor)
        nodo.debajo = self._tope
        self._tope = nodo
        self._tamano += 1

    def desapilar(self):
        """Quita y devuelve el valor de encima. O(1)."""
        if self._tope is None:
            raise IndexError("La pila está vacía")
        nodo = self._tope
        self._tope = nodo.debajo
        self._tamano -= 1
        return nodo.valor

    def ver_tope(self):
        """Devuelve el valor de encima sin quitarlo. O(1)."""
        if self._tope is None:
            raise IndexError("La pila está vacía")
        return self._tope.valor

    def esta_vacia(self):
        """O(1)."""
        return self._tope is None

    def vaciar(self):
        """Descarta todo. O(1) (el recolector libera los nodos)."""
        self._tope = None
        self._tamano = 0

    def __len__(self):
        """O(1) con contador."""
        return self._tamano

    def __iter__(self):
        """Del tope hacia el fondo. O(n)."""
        actual = self._tope
        while actual is not None:
            yield actual.valor
            actual = actual.debajo
