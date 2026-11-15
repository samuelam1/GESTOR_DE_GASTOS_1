import unicodedata
from src.modelos.validaciones import validar_texto

CATEGORIAS_POR_DEFECTO = ("Comida","Transporte","Hogar","Ocio","Salud","Otros")
CATEGORIA_OTROS = "Otros"

def clave_comparacion(nombre):
    descompuesto = unicodedata.normalize("NFD", nombre.strip())
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_tildes.casefold()

_CLAVES_POR_DEFECTO = frozenset(clave_comparacion(n) for n in CATEGORIAS_POR_DEFECTO)



class Categoria:
    def __init__(self,nombre):
        self.nombre = validar_texto(nombre,"El nombre de la categoría")
        
    @property
    def es_por_defecto(self):
        return clave_comparacion(self.nombre) in _CLAVES_POR_DEFECTO
    
    @property
    def es_eliminable(self):
        return not self.es_por_defecto
    
    def a_texto(self):
        return self.nombre
    
    @classmethod
    def desde_texto(cls,texto):
        return cls(texto)
    
    def __eq__(self,otro):
        return(isinstance(otro, Categoria)
               and clave_comparacion(self.nombre) == clave_comparacion(otro.nombre))
    
    def __hash__(self):
        return hash(clave_comparacion(self.nombre))
    
    def __repr__(self):
        return f"Categoría({self.nombre!r})"

def categorias_iniciales():
    return [Categoria(nombre) for nombre in CATEGORIAS_POR_DEFECTO]
