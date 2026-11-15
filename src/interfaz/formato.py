from decimal import Decimal, InvalidOperation


def formatear_monto(monto):
    """25000 -> '$25.000' (separador de miles al estilo colombiano)."""
    return "$" + f"{monto:,}".replace(",", ".")


def leer_monto(texto):
    """Texto -> Decimal. Acepta '25000', '25000.50' y '$ 25000'."""
    limpio = texto.replace("$", "").replace(" ", "")
    try:
        return Decimal(limpio)
    except InvalidOperation:
        raise ValueError("Escribe un número, por ejemplo 25000")
