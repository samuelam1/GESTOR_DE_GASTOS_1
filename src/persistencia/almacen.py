import json
import os
import time
from datetime import date

from src.modelos.categoria import (
    CATEGORIAS_POR_DEFECTO,
    Categoria,
    clave_comparacion,
)
from src.modelos.gasto import Gasto
from src.modelos.recurrente import Recurrente
from src.servicios.gestor import Gestor


class ErrorDeDatos(ValueError):
    """El archivo existe pero no se puede usar (corrupto o inconsistente)."""


def a_dict(gestor):
    """Estado como listas planas, con los nombres de docs/diseno.md. O(n + r)."""
    return {
        "siguienteIdGasto": gestor.gastos.siguiente_id(),
        "siguienteIdRecurrente": gestor.recurrentes.siguiente_id(),
        "categorias": gestor.gastos.categorias(),
        "gastos": [g.a_dict() for g in gestor.gastos.bitacora()],
        "recurrentes": [r.a_dict() for r in gestor.recurrentes.listar()],
    }


def guardar(gestor, ruta):
    """Escribe el JSON de forma segura: primero un temporal y luego lo
    reemplaza, para no dejar un archivo a medias. O(n + r)."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    temporal = ruta + ".tmp"
    with open(temporal, "w", encoding="utf-8") as archivo:
        json.dump(a_dict(gestor), archivo, ensure_ascii=False, indent=2)
    _reemplazar(temporal, ruta)


def _reemplazar(temporal, ruta, intentos=8):
    """os.replace con reintentos: en Windows, OneDrive o un antivirus
    pueden bloquear el archivo unos instantes (Acceso denegado)."""
    for intento in range(intentos):
        try:
            os.replace(temporal, ruta)
            return
        except PermissionError:
            if intento == intentos - 1:
                _quitar_si_existe(temporal)
                raise
            time.sleep(0.1 * (intento + 1))


def _quitar_si_existe(ruta):
    try:
        os.remove(ruta)
    except OSError:
        pass


def cargar(ruta, reloj=date.today):
    """Lee el JSON y reconstruye árbol, meses y cola. Si no hay archivo
    (primer arranque) devuelve un gestor nuevo con las categorías por
    defecto. Si el archivo está corrupto lanza ErrorDeDatos sin tocarlo.
    O(n log n + r)."""
    if not os.path.exists(ruta):
        return Gestor(reloj)
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ErrorDeDatos(f"El archivo {ruta} no es un JSON válido: {error}")
    return desde_dict(datos, reloj)


def desde_dict(datos, reloj=date.today):
    """Valida los datos y arma un Gestor. Cualquier problema -> ErrorDeDatos."""
    try:
        return _armar(datos, reloj)
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        if isinstance(error, ErrorDeDatos):
            raise
        raise ErrorDeDatos(f"Datos inválidos: {error}")


def _armar(datos, reloj):
    if not isinstance(datos, dict):
        raise ErrorDeDatos("El archivo debe contener un objeto JSON")
    categorias = _leer_categorias(_campo(datos, "categorias"))
    claves = {clave_comparacion(n): n for n in categorias}
    gastos = _leer_gastos(_campo(datos, "gastos"), claves)
    recurrentes = _leer_recurrentes(_campo(datos, "recurrentes"), claves)
    _revisar_vinculos(gastos, recurrentes)
    sig_gasto = _leer_contador(datos, "siguienteIdGasto", gastos)
    sig_recurrente = _leer_contador(datos, "siguienteIdRecurrente", recurrentes)
    gestor = Gestor(reloj)
    gestor.gastos.cargar(categorias, gastos, sig_gasto)
    gestor.recurrentes.cargar(recurrentes, sig_recurrente)
    return gestor


def _campo(datos, nombre):
    if nombre not in datos:
        raise ErrorDeDatos(f"Falta el campo '{nombre}'")
    return datos[nombre]


def _lista(valor, nombre):
    if not isinstance(valor, list):
        raise ErrorDeDatos(f"'{nombre}' debe ser una lista")
    return valor


def _leer_categorias(crudas):
    nombres = [Categoria.desde_texto(t).nombre for t in _lista(crudas, "categorias")]
    claves = [clave_comparacion(n) for n in nombres]
    if len(set(claves)) != len(claves):
        raise ErrorDeDatos("Hay categorías repetidas")
    for obligatoria in CATEGORIAS_POR_DEFECTO:
        if clave_comparacion(obligatoria) not in claves:
            raise ErrorDeDatos(f"Falta la categoría '{obligatoria}'")
    return nombres


def _leer_gastos(crudos, claves):
    gastos = [Gasto.desde_dict(d) for d in _lista(crudos, "gastos")]
    _sin_ids_repetidos(gastos, "gasto")
    for gasto in gastos:
        gasto.categoria = _categoria_conocida(gasto.categoria, claves)
    return gastos


def _leer_recurrentes(crudos, claves):
    recurrentes = [Recurrente.desde_dict(d) for d in _lista(crudos, "recurrentes")]
    _sin_ids_repetidos(recurrentes, "recurrente")
    for recurrente in recurrentes:
        recurrente.categoria = _categoria_conocida(recurrente.categoria, claves)
    return recurrentes


def _categoria_conocida(nombre, claves):
    clave = clave_comparacion(nombre)
    if clave not in claves:
        raise ErrorDeDatos(f"La categoría '{nombre}' no está en la lista")
    return claves[clave]


def _sin_ids_repetidos(elementos, nombre):
    vistos = set()
    for elemento in elementos:
        if elemento.id in vistos:
            raise ErrorDeDatos(f"Hay {nombre}s con el id {elemento.id} repetido")
        vistos.add(elemento.id)


def _revisar_vinculos(gastos, recurrentes):
    ids = {r.id for r in recurrentes}
    for gasto in gastos:
        if gasto.recurrente_id is not None and gasto.recurrente_id not in ids:
            raise ErrorDeDatos(
                f"El gasto {gasto.id} apunta al recurrente inexistente "
                f"{gasto.recurrente_id}")


def _leer_contador(datos, nombre, elementos):
    valor = _campo(datos, nombre)
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ErrorDeDatos(f"'{nombre}' debe ser un entero positivo")
    mayor = max((e.id for e in elementos), default=0)
    if valor <= mayor:
        raise ErrorDeDatos(f"'{nombre}' ({valor}) no puede ser menor o igual "
                           f"que el mayor id existente ({mayor})")
    return valor
