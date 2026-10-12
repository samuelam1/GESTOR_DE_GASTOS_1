from src.validaciones import (
    validar_fecha,
    validar_id,
    validar_monto,
    validar_texto,
    )

ORIGENES = ("diario","recurrente")


class Gasto:

    def __init__(self,id,monto,fecha,categoria,descripcion, origen="diario", recurrente_id=None):
        self.id = validar_id(id)
        self.monto = validar_monto
        self.fecha = validar_fecha(fecha)
        self.categoria = validar_texto(categoria, "La categoría")
        self.descripcion = validar_texto(descripcion,"La descripción")
        self._asignar_origen(origen, recurrente_id)
        
        
    def _asignar_origen(self,origen,recurrente_id):
        if origen not in ORIGENES:
            raise ValueError("El origen debe ser 'diario' o 'recurrente' ")
        if origen == "diario" and recurrente_id is not None:
            raise ValueError("Un gasto diario no tiene recurrente_id")
        if origen == "recurrente":
            validar_id(recurrente_id,"recurrente_id")
        
        self.origen = origen
        self.recurrente_id = recurrente_id
        
    def a_dict(self):
        return {
            "id":self.id,
            "monto":self.monto,
            "fecha":self.fecha.isoformat(),
            "categoria":self.categoria,
            "descripcion":self.descripcion,
            "origen":self.origen,
            "recurrenteId": self.recurrente_id
            }
    
    @classmethod
    def desde_dict(cls,datos):
        try:
            return cls(
                id = datos["id"],
                monto = datos["monto"],
                fecha = datos["fecha"],
                categoria = datos["categoria"],
                descripcion = datos["descripcion"],
                origen= datos["origen"],
                recurrente_id=datos["recurrenteId"],
                )
        except KeyError as error:
            raise ValueError (f"falta el campo {error} en el gasto")
        
    def _eq_(self,otro):
        return isinstance(otro, Gasto) and self.a_dict() == otro.a_dict()
    
    def __repr__(self):
        return (
            f"Gasto(id={self.id}, monto={self.monto}, fecha={self.fecha}, "
            f"categoria={self.categoria!r}, origen={self.origen!r})"
        )

