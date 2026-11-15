import os

CARPETA_PROYECTO = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
RUTA_LOCAL = os.path.join(CARPETA_PROYECTO, "data", "gastos.json")
PUNTO_DE_MONTAJE = "/content/drive"
RUTA_EN_DRIVE = os.path.join(PUNTO_DE_MONTAJE, "MyDrive", "GestorGastos", "gastos.json")


def _drive_de_colab():
    try:
        from google.colab import drive

        return drive
    except ImportError:
        return None


def ruta_de_datos(
    drive=None,
    punto_de_montaje=PUNTO_DE_MONTAJE,
    ruta_en_drive=RUTA_EN_DRIVE,
    ruta_local=RUTA_LOCAL,
):

    drive = drive if drive is not None else _drive_de_colab()
    if drive is None:
        return ruta_local
    drive.mount(punto_de_montaje)
    return ruta_en_drive
