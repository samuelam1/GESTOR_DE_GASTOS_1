from src.interfaz.formato import formatear_monto, leer_monto  # noqa: F401
from src.modelos.validaciones import validar_fecha
from src.persistencia import almacen


class Consola:
    """Menú de texto. Es la única capa que usa print e input; `entrada` y
    `salida` se inyectan para poder probarla con respuestas escritas de
    antemano. Solo habla con el Gestor y el almacén."""

    def __init__(self, gestor, ruta, entrada=input, salida=print):
        self.gestor = gestor
        self.ruta = ruta
        self._entrada = entrada
        self._salida = salida

    # ---------- Entrada y salida ----------

    def _decir(self, texto=""):
        self._salida(texto)

    def _pedir(self, pregunta, por_defecto=None):
        sufijo = f" [{por_defecto}]" if por_defecto is not None else ""
        respuesta = self._entrada(f"{pregunta}{sufijo}: ").strip()
        return respuesta if respuesta else por_defecto

    def _pedir_fecha(self, pregunta="Fecha (AAAA-MM-DD)", por_defecto=None):
        texto = self._pedir(pregunta, por_defecto)
        return validar_fecha(texto)

    def _pedir_categoria(self, por_defecto=None):
        nombres = self.gestor.gastos.categorias()
        for numero, nombre in enumerate(nombres, start=1):
            self._decir(f"  {numero}. {nombre}")
        texto = self._pedir("Categoría (número o nombre)", por_defecto)
        if texto is not None and texto.isdigit():
            indice = int(texto)
            if not 1 <= indice <= len(nombres):
                raise ValueError("Ese número de categoría no existe")
            return nombres[indice - 1]
        return texto

    def _pedir_id(self, pregunta="Id del gasto"):
        texto = self._pedir(pregunta)
        if texto is None or not texto.isdigit():
            raise ValueError("El id debe ser un número entero")
        return int(texto)

    def _mostrar_gasto(self, gasto):
        etiqueta = "recurrente" if gasto.origen == "recurrente" else "diario"
        self._decir(
            f"  #{gasto.id:<4} {gasto.fecha}  {formatear_monto(gasto.monto):>12}  "
            f"{gasto.categoria:<12} {gasto.descripcion}  [{etiqueta}]")

    def _mostrar_gastos(self, gastos, vacio="No hay gastos."):
        if not gastos:
            self._decir(vacio)
            return
        for gasto in gastos:
            self._mostrar_gasto(gasto)
        total = sum(g.monto for g in gastos)
        self._decir(f"  {len(gastos)} gasto(s), total {formatear_monto(total)}")

    # ---------- Bucle principal ----------

    def _acciones(self):
        return {
            "1": ("Registrar gasto", self.registrar),
            "2": ("Editar gasto", self.editar),
            "3": ("Borrar gasto", self.borrar),
            "4": ("Buscar por descripción", self.buscar),
            "5": ("Filtrar por categoría", self.filtrar),
            "6": ("Consultar rango de fechas", self.rango),
            "7": ("Navegar por meses", self.navegar_meses),
            "8": ("Bitácora completa", self.bitacora),
            "9": ("Recurrentes", self.menu_recurrentes),
            "10": ("Categorías", self.menu_categorias),
            "11": ("Deshacer", self.deshacer),
            "0": ("Salir", None),
        }

    def ejecutar(self):
        """Bucle del menú. Guarda el archivo después de cada acción."""
        self._decir("=== Gestor de Gastos ===")
        self.mostrar_pendientes()
        acciones = self._acciones()
        while True:
            self._decir()
            for clave, (nombre, _) in acciones.items():
                self._decir(f"{clave:>2}. {nombre}")
            opcion = self._pedir("Opción")
            if opcion == "0":
                break
            if opcion not in acciones:
                self._decir("Opción no válida.")
                continue
            self._ejecutar_accion(acciones[opcion][1])
        self._decir("Hasta luego.")

    def _ejecutar_accion(self, accion):
        try:
            accion()
            almacen.guardar(self.gestor, self.ruta)
        except ValueError as error:
            self._decir(f"Error: {error}")
        except OSError as error:
            self._decir(f"No se pudo guardar el archivo: {error}")

    # ---------- Gastos ----------

    def registrar(self):
        hoy = self.gestor.reloj()
        monto = leer_monto(self._pedir("Monto en COP") or "")
        fecha = self._pedir_fecha(por_defecto=hoy.isoformat())
        categoria = self._pedir_categoria()
        descripcion = self._pedir("Descripción") or ""
        gasto = self.gestor.gastos.registrar(monto, fecha, categoria, descripcion)
        self._decir("Registrado:")
        self._mostrar_gasto(gasto)

    def editar(self):
        id_gasto = self._pedir_id()
        actual = self.gestor.gastos.buscar_por_id(id_gasto)
        if actual is None:
            raise ValueError(f"No existe el gasto {id_gasto}")
        self._decir("Enter deja el valor actual.")
        monto = self._pedir("Monto", str(actual.monto))
        fecha = self._pedir("Fecha", actual.fecha.isoformat())
        categoria = self._pedir_categoria(actual.categoria)
        descripcion = self._pedir("Descripción", actual.descripcion)
        nuevo = self.gestor.gastos.editar(
            id_gasto, monto=leer_monto(monto), fecha=fecha,
            categoria=categoria, descripcion=descripcion)
        self._decir("Actualizado:")
        self._mostrar_gasto(nuevo)

    def borrar(self):
        id_gasto = self._pedir_id()
        gasto = self.gestor.borrar_gasto(id_gasto)
        self._decir("Borrado (puedes deshacerlo):")
        self._mostrar_gasto(gasto)

    def buscar(self):
        texto = self._pedir("Texto a buscar en la descripción") or ""
        self._mostrar_gastos(self.gestor.gastos.buscar_por_descripcion(texto),
                             "Sin resultados.")

    def filtrar(self):
        categoria = self._pedir_categoria()
        self._mostrar_gastos(self.gestor.gastos.filtrar_por_categoria(categoria),
                             "Sin gastos en esa categoría.")

    def rango(self):
        desde = self._pedir_fecha("Desde (AAAA-MM-DD)")
        hasta = self._pedir_fecha("Hasta (AAAA-MM-DD)")
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la final")
        self._mostrar_gastos(self.gestor.gastos.consultar_rango(desde, hasta),
                             "No hay gastos en ese rango.")

    def bitacora(self):
        self._mostrar_gastos(self.gestor.gastos.bitacora(),
                             "La bitácora está vacía.")

    def deshacer(self):
        resultado = self.gestor.deshacer()
        if resultado is None:
            self._decir("No hay nada que deshacer.")
            return
        operacion, gasto = resultado
        self._decir(f"Deshecho ({operacion}):")
        self._mostrar_gasto(gasto)

    # ---------- Meses ----------

    def navegar_meses(self):
        nav = self.gestor.gastos.meses
        while True:
            self._decir(f"Mes {nav.mes_actual()}: total "
                        f"{formatear_monto(nav.total_actual())}")
            self._mostrar_gastos(nav.gastos_actual(), "  (sin gastos este mes)")
            opcion = (self._pedir("[a] anterior, [s] siguiente, [q] volver") or "q").lower()
            if opcion == "a":
                if not nav.anterior():
                    self._decir("Ya estás en el primer mes.")
            elif opcion == "s":
                if not nav.siguiente():
                    self._decir("Ya estás en el último mes.")
            elif opcion == "q":
                return
            else:
                self._decir("Escribe a, s o q.")

    # ---------- Recurrentes ----------

    def mostrar_pendientes(self):
        pendientes = self.gestor.recurrentes.pendientes()
        if not pendientes:
            return
        self._decir("Recurrentes pendientes de este mes:")
        for r in pendientes:
            nota = f" - {r.nota}" if r.nota else ""
            self._decir(f"  #{r.id} día {r.dia}: {r.descripcion} "
                        f"{formatear_monto(r.monto)}{nota}")

    def menu_recurrentes(self):
        self._decir("a) Añadir  b) Listar activos  c) Terminar  "
                    "d) Pendientes  e) Pagar")
        opcion = (self._pedir("Opción") or "").lower()
        acciones = {"a": self._recurrente_agregar, "b": self._recurrente_listar,
                    "c": self._recurrente_terminar, "d": self._recurrente_pendientes,
                    "e": self._recurrente_pagar}
        if opcion not in acciones:
            raise ValueError("Opción no válida")
        acciones[opcion]()

    def _recurrente_agregar(self):
        monto = leer_monto(self._pedir("Monto mensual") or "")
        categoria = self._pedir_categoria()
        descripcion = self._pedir("Descripción") or ""
        dia_texto = self._pedir("Día del mes en que vence") or ""
        if not dia_texto.isdigit():
            raise ValueError("El día debe ser un número entre 1 y 31")
        nota = self._pedir("Nota (opcional)", "")
        r = self.gestor.recurrentes.agregar(monto, categoria, descripcion,
                                            int(dia_texto), nota)
        self._decir(f"Recurrente #{r.id} creado.")

    def _recurrente_listar(self):
        activos = self.gestor.recurrentes.listar_activos()
        if not activos:
            self._decir("No hay recurrentes activos.")
        for r in activos:
            self._decir(f"  #{r.id} día {r.dia}: {r.descripcion} "
                        f"{formatear_monto(r.monto)} [{r.categoria}] {r.nota}")

    def _recurrente_terminar(self):
        r = self.gestor.recurrentes.terminar(self._pedir_id("Id del recurrente"))
        self._decir(f"Recurrente #{r.id} terminado.")

    def _recurrente_pendientes(self):
        if not self.gestor.recurrentes.pendientes():
            self._decir("No hay pendientes este mes.")
        self.mostrar_pendientes()

    def _recurrente_pagar(self):
        id_rec = self._pedir_id("Id del recurrente a pagar")
        plantilla = self.gestor.recurrentes.buscar(id_rec)
        if plantilla is None:
            raise ValueError(f"No existe el recurrente {id_rec}")
        monto = leer_monto(self._pedir("Monto", str(plantilla.monto)))
        fecha = self._pedir_fecha(por_defecto=self.gestor.reloj().isoformat())
        gasto = self.gestor.recurrentes.pagar(id_rec, monto=monto, fecha=fecha)
        self._decir("Pago registrado:")
        self._mostrar_gasto(gasto)

    # ---------- Categorías ----------

    def menu_categorias(self):
        self._decir("a) Listar  b) Crear  c) Eliminar")
        opcion = (self._pedir("Opción") or "").lower()
        if opcion == "a":
            for nombre in self.gestor.gastos.categorias():
                self._decir(f"  {nombre}")
        elif opcion == "b":
            nombre = self.gestor.gastos.agregar_categoria(
                self._pedir("Nombre de la categoría") or "")
            self._decir(f"Categoría '{nombre}' creada.")
        elif opcion == "c":
            nombre = self._pedir_categoria()
            movidos = self.gestor.eliminar_categoria(nombre)
            self._decir(f"Categoría eliminada; {movidos} gasto(s) pasaron a 'Otros'.")
        else:
            raise ValueError("Opción no válida")
