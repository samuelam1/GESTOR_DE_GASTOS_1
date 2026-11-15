from datetime import date

from src.estructuras.arbol_fechas import ArbolFechas
from src.estructuras.pila import Pila
from src.modelos.categoria import (
    CATEGORIA_OTROS,
    Categoria,
    categorias_iniciales,
    clave_comparacion,
)
from src.modelos.gasto import Gasto
from src.modelos.validaciones import validar_fecha, validar_id, validar_texto
from src.servicios.meses import NavegadorMeses, limites_del_mes, mes_de


class ServicioGastos:
    """Registrar, editar, borrar, buscar, filtrar, totales, categorías y deshacer.

    No usa print ni input. Los resultados que se devuelven como `list` son
    copias para quien consulta; el almacenamiento real es el árbol por fecha.
    Los ids no se reutilizan: deshacer un registro no baja el contador.
    """

    def __init__(self, reloj=date.today):
        self._reloj = reloj
        self._arbol = ArbolFechas()
        self._categorias = categorias_iniciales()
        self._siguiente_id = 1
        self._deshacer = Pila()
        self.meses = NavegadorMeses(self, mes_de(reloj()))

    # ---------- Categorías ----------

    def categorias(self):
        """Nombres de las categorías, en orden de creación. O(c)."""
        return [c.nombre for c in self._categorias]

    def resolver_categoria(self, nombre):
        """Nombre canónico de la categoría (sin importar mayúsculas ni
        tildes); ValueError si no existe. O(c)."""
        validar_texto(nombre, "La categoría")
        buscada = clave_comparacion(nombre)
        for categoria in self._categorias:
            if clave_comparacion(categoria.nombre) == buscada:
                return categoria.nombre
        raise ValueError(f"La categoría '{nombre}' no existe")

    def agregar_categoria(self, nombre):
        """Crea una categoría; ValueError si ya existe. O(c)."""
        nueva = Categoria(nombre)
        if nueva in self._categorias:
            raise ValueError(f"La categoría '{nueva.nombre}' ya existe")
        self._categorias.append(nueva)
        return nueva.nombre

    def quitar_categoria(self, nombre):
        """Quita la categoría de la lista (no toca los gastos; eso lo hace
        el Gestor). 'Otros' y las de por defecto no se pueden quitar. O(c)."""
        canonico = self.resolver_categoria(nombre)
        categoria = Categoria(canonico)
        if not categoria.es_eliminable:
            raise ValueError(f"La categoría '{canonico}' no se puede eliminar")
        self._categorias.remove(categoria)
        return canonico

    def reasignar_categoria(self, origen, destino):
        """Cambia la categoría de todos los gastos que la usan. Devuelve
        cuántos cambió. O(n)."""
        clave = clave_comparacion(origen)
        cambiados = 0
        for gasto in self._arbol.en_orden():
            if clave_comparacion(gasto.categoria) == clave:
                gasto.categoria = destino
                cambiados += 1
        return cambiados

    # ---------- Gastos ----------

    def registrar(self, monto, fecha, categoria, descripcion,
                  origen="diario", recurrente_id=None):
        """Crea un gasto con id nuevo, lo guarda y lo registra para deshacer.
        O(h) más O(m) por el mes."""
        gasto = Gasto(
            id=self._siguiente_id,
            monto=monto,
            fecha=fecha,
            categoria=self.resolver_categoria(categoria),
            descripcion=descripcion,
            origen=origen,
            recurrente_id=recurrente_id,
        )
        self._siguiente_id += 1
        self._insertar(gasto)
        self._deshacer.apilar(("registrar", gasto.id))
        return gasto

    def _insertar(self, gasto):
        self._arbol.insertar(gasto)
        self.meses.registrar_mes(mes_de(gasto.fecha))

    def buscar_por_id(self, id_gasto):
        """El gasto con ese id, o None. Recorre todo el árbol: O(n)."""
        for gasto in self._arbol.en_orden():
            if gasto.id == id_gasto:
                return gasto
        return None

    def _exigir(self, id_gasto):
        validar_id(id_gasto)
        gasto = self.buscar_por_id(id_gasto)
        if gasto is None:
            raise ValueError(f"No existe el gasto {id_gasto}")
        return gasto

    def editar(self, id_gasto, monto=None, fecha=None, categoria=None,
               descripcion=None):
        """Cambia los campos dados (None = no tocar). Devuelve el gasto nuevo.
        O(n) por buscar el id, más O(h) por reubicarlo."""
        antes = self._exigir(id_gasto)
        nuevo = Gasto(
            id=antes.id,
            monto=antes.monto if monto is None else monto,
            fecha=antes.fecha if fecha is None else fecha,
            categoria=antes.categoria if categoria is None
            else self.resolver_categoria(categoria),
            descripcion=antes.descripcion if descripcion is None else descripcion,
            origen=antes.origen,
            recurrente_id=antes.recurrente_id,
        )
        self._arbol.eliminar(antes.fecha, antes.id)
        self._insertar(nuevo)
        self._deshacer.apilar(("editar", antes))
        return nuevo

    def borrar(self, id_gasto):
        """Quita el gasto y lo devuelve. O(n) por buscar el id."""
        gasto = self._exigir(id_gasto)
        self._arbol.eliminar(gasto.fecha, gasto.id)
        self._deshacer.apilar(("borrar", gasto))
        return gasto

    # ---------- Deshacer ----------

    def hay_que_deshacer(self):
        """O(1)."""
        return not self._deshacer.esta_vacia()

    def deshacer(self):
        """Revierte la última operación. Devuelve (operación, gasto) o None
        si no hay nada que deshacer. O(n) por buscar el id; apilar y
        desapilar son O(1)."""
        if self._deshacer.esta_vacia():
            return None
        operacion, dato = self._deshacer.desapilar()
        if operacion == "registrar":
            gasto = self._exigir(dato)
            self._arbol.eliminar(gasto.fecha, gasto.id)
            return operacion, gasto
        restaurado = self._con_categoria_vigente(dato)
        if operacion == "editar":
            actual = self._exigir(restaurado.id)
            self._arbol.eliminar(actual.fecha, actual.id)
        self._insertar(restaurado)
        return operacion, restaurado

    def _con_categoria_vigente(self, gasto):
        """Si la categoría se eliminó mientras tanto, el gasto vuelve en 'Otros'."""
        try:
            gasto.categoria = self.resolver_categoria(gasto.categoria)
        except ValueError:
            gasto.categoria = CATEGORIA_OTROS
        return gasto

    # ---------- Consultas ----------

    def bitacora(self):
        """Todos los gastos, de más antiguo a más reciente. O(n)."""
        return list(self._arbol.en_orden())

    def consultar_rango(self, desde, hasta):
        """Gastos con desde <= fecha <= hasta. O(h + k)."""
        return list(self._arbol.consultar_rango(
            validar_fecha(desde), validar_fecha(hasta)))

    def total_rango(self, desde, hasta):
        """Suma en COP del rango inclusivo. O(h + k)."""
        return self._arbol.total_rango(validar_fecha(desde), validar_fecha(hasta))

    def gastos_del_mes(self, anio, mes):
        """O(h + k)."""
        primero, ultimo = limites_del_mes(anio, mes)
        return self.consultar_rango(primero, ultimo)

    def total_mes(self, anio, mes):
        """O(h + k)."""
        primero, ultimo = limites_del_mes(anio, mes)
        return self.total_rango(primero, ultimo)

    def buscar_por_descripcion(self, texto):
        """Coincidencia parcial sin distinguir mayúsculas ni tildes.
        Recorre todo el árbol: O(n)."""
        buscado = clave_comparacion(validar_texto(texto, "El texto a buscar"))
        return [g for g in self._arbol.en_orden()
                if buscado in clave_comparacion(g.descripcion)]

    def filtrar_por_categoria(self, categoria):
        """O(n)."""
        clave = clave_comparacion(self.resolver_categoria(categoria))
        return [g for g in self._arbol.en_orden()
                if clave_comparacion(g.categoria) == clave]

    def cantidad(self):
        """O(1)."""
        return len(self._arbol)

    def altura_arbol(self):
        """Altura del árbol, para mostrar su degeneración. O(n)."""
        return self._arbol.altura()

    # ---------- Persistencia ----------

    def siguiente_id(self):
        return self._siguiente_id

    def cargar(self, categorias, gastos, siguiente_id):
        """Reemplaza el estado con datos ya validados (vacía 'deshacer').

        Los gastos se insertan empezando por el del medio de la lista
        ordenada por fecha, para que el árbol salga casi balanceado en vez
        de degenerado. O(n log n)."""
        self._categorias = [Categoria(nombre) for nombre in categorias]
        self._siguiente_id = siguiente_id
        self._deshacer.vaciar()
        self._arbol = ArbolFechas()
        ordenados = sorted(gastos, key=lambda g: (g.fecha, g.id))
        self._insertar_por_mitades(ordenados, 0, len(ordenados) - 1)

    def _insertar_por_mitades(self, gastos, inicio, fin):
        if inicio > fin:
            return
        medio = (inicio + fin) // 2
        self._insertar(gastos[medio])
        self._insertar_por_mitades(gastos, inicio, medio - 1)
        self._insertar_por_mitades(gastos, medio + 1, fin)
