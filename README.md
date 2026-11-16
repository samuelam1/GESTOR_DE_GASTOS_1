# Gestor de Gastos

Aplicación en Python para registrar y consultar gastos personales en pesos colombianos (COP). Funciona de dos formas: por **consola** (menú de texto) o con una **interfaz gráfica en Google Colab** (pestañas con `ipywidgets`).

Es también un proyecto de **estructuras de datos**: las estructuras principales (lista simple, lista doble, pila, cola y árbol binario de búsqueda) están implementadas desde cero, sin usar `list`, `dict` ni `deque` de Python para almacenar sus datos.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/samuelam1/GESTOR_DE_GASTOS_1/blob/main/Gestor_de_Gastos.ipynb)

---

## Funcionalidades

- **Gastos:** registrar, editar, borrar y deshacer la última operación.
- **Consultas:** buscar por descripción, filtrar por categoría, consultar por rango de fechas y ver la bitácora completa.
- **Navegación por meses:** avanzar y retroceder entre meses con su total.
- **Gastos recurrentes:** obligaciones mensuales (arriendo, internet, etc.) con una cola de pendientes del mes. El gasto solo se crea cuando se paga.
- **Categorías:** 6 por defecto (`Comida`, `Transporte`, `Hogar`, `Ocio`, `Salud`, `Otros`) y las que quieras crear. Al eliminar una, sus gastos pasan a `Otros`.
- **Búsquedas flexibles:** ignoran mayúsculas y tildes.
- **Persistencia en JSON:** guardado seguro (archivo temporal + reemplazo) y validación completa al cargar; si el archivo está corrupto, no se modifica.

---

## Cómo ejecutarlo

### Opción 1: Consola

Requisitos: **Python 3.8 o superior**. La versión de consola solo usa la biblioteca estándar.

```bash
git clone https://github.com/samuelam1/GESTOR_DE_GASTOS_1.git
cd GESTOR_DE_GASTOS_1
python main.py
```

Los datos se guardan en `data/gastos.json` (se crea solo la primera vez). Se guarda automáticamente después de cada acción.

### Opción 2: Interfaz gráfica en Google Colab

1. Abre el notebook con el botón **Abrir en Colab** de arriba.
2. Ejecuta todas las celdas en orden (*Entorno de ejecución → Ejecutar todo*).
3. Autoriza el acceso a Google Drive cuando Colab lo pida.

Tus datos quedan en **tu** Drive, en `MyDrive/GestorGastos/gastos.json`, y se conservan entre sesiones.

> La interfaz gráfica usa `ipywidgets`, que ya viene instalado en Colab.

---

## Menú de la consola

```
 1. Registrar gasto            7. Navegar por meses
 2. Editar gasto               8. Bitácora completa
 3. Borrar gasto               9. Recurrentes
 4. Buscar por descripción    10. Categorías
 5. Filtrar por categoría     11. Deshacer
 6. Consultar rango de fechas  0. Salir
```

Los montos se escriben como `25000`, `25000.50` o `$ 25000` y se muestran con formato colombiano (`$25.000`). Las fechas usan el formato `AAAA-MM-DD`.

---

## Estructuras de datos

| Estructura | Archivo | Para qué se usa |
|---|---|---|
| Árbol binario de búsqueda | `estructuras/arbol_fechas.py` | Almacena los gastos por fecha (un nodo = un día). Permite consultas por rango en `O(h + k)` |
| Lista simple | `estructuras/lista_simple.py` | Guarda los gastos de un mismo día dentro de cada nodo del árbol |
| Lista doble con cursor | `estructuras/lista_doble.py` | Navegación entre meses (`AAAA-MM`) hacia adelante y hacia atrás |
| Pila | `estructuras/pila.py` | Historial para **deshacer**; también el recorrido en orden del árbol sin recursión |
| Cola | `estructuras/cola.py` | Recurrentes pendientes del mes, ordenados por fecha de vencimiento; también el recorrido por niveles para calcular la altura del árbol |

Detalles de diseño:

- Al cargar desde el archivo, los gastos se insertan empezando por el del medio de la lista ordenada, para que el árbol quede casi balanceado en lugar de degenerar en una lista.
- Los montos son **enteros en COP** (se redondean con `ROUND_HALF_UP`).
- Los ids no se reutilizan, ni siquiera después de deshacer.
- Un recurrente con día 31 en un mes corto vence el último día de ese mes.

---

## Estructura del proyecto

```
GESTOR_DE_GASTOS_1/
├── main.py                    # Punto de entrada (consola)
├── Gestor_de_Gastos.ipynb     # Notebook para Google Colab
├── data/
│   └── gastos.json            # Datos locales (se crea al usar la app)
└── src/
    ├── estructuras/           # Pila, cola, listas y árbol de fechas
    ├── modelos/               # Gasto, Recurrente, Categoria y validaciones
    ├── servicios/             # Lógica: gastos, recurrentes, meses y Gestor
    ├── persistencia/          # Lectura/escritura del JSON y rutas de datos
    └── interfaz/              # Consola, interfaz gráfica (Colab) y formato
```

La arquitectura está en capas: la **interfaz** solo habla con el `Gestor` y el almacén; los **servicios** no usan `print` ni `input`; los **modelos** validan sus propios datos.

---

## Formato de los datos

```json
{
  "siguienteIdGasto": 2,
  "siguienteIdRecurrente": 2,
  "categorias": ["Comida", "Transporte", "Hogar", "Ocio", "Salud", "Otros"],
  "gastos": [
    {
      "id": 1,
      "monto": 25000,
      "fecha": "2026-11-15",
      "categoria": "Comida",
      "descripcion": "Almuerzo",
      "origen": "diario",
      "recurrenteId": null
    }
  ],
  "recurrentes": [
    {
      "id": 1,
      "monto": 800000,
      "categoria": "Hogar",
      "descripcion": "Arriendo",
      "dia": 5,
      "nota": "",
      "activo": true
    }
  ]
}
```

---

## Autores

- Samuel Alvarez
- Valentina Palacio
- Stiven Romero
