from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, datetime


def validar_texto(valor, nombre):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} no puede estar vacía")
    return valor.strip()    

def validar_fecha(fecha):
    
    if isinstance(fecha, date):
        return fecha
    
    if isinstance(fecha, datetime):
        return fecha.date()
    
    if isinstance(fecha, str):
        try:
            return datetime.strptime(fecha, "%y-%m-%d").date()
        except ValueError:
         raise ("La fecha debe tener formato AAAA-MM-DD")
            
    raise ValueError("La fecha debe ser un date o un texto AAAA-MM-DD")
      

def redondear_monto(monto):
    if isinstance(monto, bool) or not isinstance(monto, (int,float,Decimal)):
        raise ValueError("El monto debe ser un número")
    try:
        entero = Decimal(str(monto)).quantize(Decimal(1),rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("El monto debe ser un número")
    return int(entero)

def validar_monto(monto):
    entero = redondear_monto(monto)
    
    if entero <= 0:
        raise ValueError("El monto debe ser mayor a cero")
    return entero


def validar_id(valor, nombre="id"):
    if isinstance (valor,str) or not isinstance(valor, int) or valor < 1:
        raise ValueError(f"{nombre} debe ser un entero positivo")
    return valor


