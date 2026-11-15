class NodoCola:
    """Un elemento de la cola y el que está detrás (o None)."""

    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class Cola:
    """Cola (FIFO) enlazada con referencia al frente y al final.

    - desencolar y ver_frente en una cola vacía lanzan IndexError.
    - No usa list, dict ni deque de Python.
    """

    def __init__(self):
        """O(1)."""
        self._frente = None
        self._final = None
        self._tamano = 0

    def encolar(self, valor):
        """Agrega al final. O(1) gracias a la referencia al final."""
        nodo = NodoCola(valor)
        if self._final is None:
            self._frente = nodo
        else:
            self._final.siguiente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self):
        """Quita y devuelve el del frente. O(1)."""
        if self._frente is None:
            raise IndexError("La cola está vacía")
        nodo = self._frente
        self._frente = nodo.siguiente
        if self._frente is None:
            self._final = None
        self._tamano -= 1
        return nodo.valor

    def ver_frente(self):
        """Devuelve el del frente sin quitarlo. O(1)."""
        if self._frente is None:
            raise IndexError("La cola está vacía")
        return self._frente.valor

    def esta_vacia(self):
        """O(1)."""
        return self._frente is None

    def vaciar(self):
        """Descarta todo. O(1)."""
        self._frente = None
        self._final = None
        self._tamano = 0

    def __len__(self):
        """O(1) con contador."""
        return self._tamano

    def __iter__(self):
        """Del frente al final, sin consumir la cola. O(n)."""
        actual = self._frente
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

