import calendar 
from datetime import date

from src.validaciones import (validar_id,validar_texto, validar_monto) 

def validar_dia(dia):
    if isinstance(dia, bool) or not isinstance(dia, int) or not 1 <= dia <= 31:
        raise ValueError("El día debe ser un entero entre 1 y 31")
    return dia

def validar_nota(nota):
    if nota is None:
        return ""
    if not isinstance(nota, str):
        raise ValueError("La nota debe ser un texto")
    return nota.strip()

def validar_activo(activo):
    if not isinstance(activo, bool):
      raise ValueError ("Activo debe ser True o False")
    return activo

class Recurrente:
    def __init__(self,id,monto,categoria,descripcion,dia,nota="",activo=True):
        self.id = validar_id(id)
        self.monto = validar_monto(monto)
        self.categoria = validar_texto(categoria, "La categoría")
        self.descripcion = validar_texto(descripcion, "La descripción")
        self.dia = validar_dia(dia)
        self.nota = validar_nota(nota)
        self.activo = validar_activo(activo)
    
    def terminar(self):
        self.activo = False
        
    def fecha_en(self,anio,mes):
        if isinstance(mes, bool) or not isinstance(mes, int) or not 1 <= mes <= 12:
            raise   ValueError("El mes debe ser un número entero entre 1 y 12")
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        return date (anio, mes, min(self.dia, ultimo_dia))
    
    def a_dict(self):
        return{
            "id": self.id,
            "monto": self.monto,
            "categoria": self.categoria,
            "descripcion": self.descripcion,
            "dia": self.dia,
            "nota": self.nota,
            "activo": self.activo,
            }
    
    def desde_dict(cls,datos):
        try:
            return cls(
                id = datos["id"],
                monto = datos["monto"],
                categoria = datos["categoria"],
                descripcion = datos["descripcion"],
                dia = datos["dia"],
                nota = datos["nota"],
                activo = datos ["activo"],
                )
        except KeyError as error:
            raise ValueError(f"Falta el campo {error} en el recurrente")
            
    def __eq__(self,otro):
        return isinstance(otro, Recurrente) and self.a_dict() == otro.a_dict()
    
    def __repr__(self):
        return(
            f"Recurrente(id={self.id}, monto={self.monto}, dia={self.dia},"
            f"descripcion={self.descripcion!r}, activo={self.activo})"
            )
            
            
R = Recurrente(1, 20000, "Electrodomestico", "Tablet en Alkomprar", 2,"pagar siempre los dos",True)

        
