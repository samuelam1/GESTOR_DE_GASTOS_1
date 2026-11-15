import os
import sys

from src.interfaz.consola import Consola
from src.persistencia import almacen

RUTA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "gastos.json")


def main():
    try:
        gestor = almacen.cargar(RUTA_DATOS)
    except almacen.ErrorDeDatos as error:
        print(f"No se pudo cargar {RUTA_DATOS}:\n  {error}")
        print("El archivo no se modificó. Corrígelo o muévelo y vuelve a abrir.")
        return 1
    try:
        Consola(gestor, RUTA_DATOS).ejecutar()
    except (EOFError, KeyboardInterrupt):
        print("\nSesión terminada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
