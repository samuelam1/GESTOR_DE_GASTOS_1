class NodoLista:
    def __init__(self,gasto):
        self.gasto = gasto
        self.siguiente = None
        
class ListaSimple:
    def __init__(self):
        self._cabeza = None
        self._tamano = 0

    def insertar(self, gasto):
        """Inserta al inicio. O(1)."""
        nodo = NodoLista(gasto)
        nodo.siguiente = self._cabeza
        self._cabeza = nodo
        self._tamano += 1

    def buscar(self, id_gasto):
        """Devuelve el gasto con ese id, o None si no está. O(n)."""
        actual = self._cabeza
        while actual is not None:
            if actual.gasto.id == id_gasto:
                return actual.gasto
            actual = actual.siguiente
        return None
        
    def eliminar(self, id_gasto):
        """Quita la primera coincidencia y devuelve el gasto quitado,
        o None si el id no existe. Casos: primero, medio, último. O(n)."""
        anterior = None
        actual = self._cabeza
        while actual is not None:
            if actual.gasto.id == id_gasto:
                if anterior is None:
                    self._cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                self._tamano -= 1
                return actual.gasto
            anterior = actual 
            actual = actual.siguiente
        return None
    
    def __iter__(self):
        """Recorre los gastos de cabeza a cola. O(n) completo."""
        actual = self._cabeza
        while actual is not None:
            yield actual.gasto
            actual = actual.siguiente
            
    def __len__(self):
        """Cantidad de gastos. O(1) si llevas un contador."""
        return self._tamano

    def esta_vacia(self):
        """True si no hay gastos. O(1)."""
        return self._cabeza is None