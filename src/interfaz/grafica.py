import html
from datetime import date

import ipywidgets as widgets

from src.interfaz.formato import formatear_monto, leer_monto
from src.modelos.categoria import Categoria
from src.persistencia import almacen

TODAS = "(todas)"
SIN_CAMBIO = "(sin cambio)"


def _poner_opciones(desplegable, opciones):
    """Cambia las opciones de un Dropdown conservando la selección si sigue
    existiendo. `opciones` es una lista de textos o de (etiqueta, valor)."""
    valores = [o[1] if isinstance(o, tuple) else o for o in opciones]
    anterior = desplegable.value
    desplegable.options = opciones
    if anterior in valores:
        desplegable.value = anterior
    elif valores:
        desplegable.value = valores[0]
    else:
        desplegable.value = None


def tabla_html(gastos, vacio="No hay gastos."):
    """Tabla de gastos con el total al final. O(k)."""
    if not gastos:
        return f"<p><i>{html.escape(vacio)}</i></p>"
    filas = []
    for g in gastos:
        etiqueta = "recurrente" if g.origen == "recurrente" else "diario"
        filas.append(
            f"<tr><td>{g.id}</td><td>{g.fecha}</td>"
            f"<td style='text-align:right'>{formatear_monto(g.monto)}</td>"
            f"<td>{html.escape(g.categoria)}</td>"
            f"<td>{html.escape(g.descripcion)}</td><td>{etiqueta}</td></tr>")
    total = sum(g.monto for g in gastos)
    return (
        "<table style='border-collapse:collapse' border='1' cellpadding='4'>"
        "<tr><th>Id</th><th>Fecha</th><th>Monto</th><th>Categoría</th>"
        "<th>Descripción</th><th>Origen</th></tr>" + "".join(filas) +
        f"<tr><td colspan='2'><b>{len(gastos)} gasto(s)</b></td>"
        f"<td style='text-align:right'><b>{formatear_monto(total)}</b></td>"
        "<td colspan='3'></td></tr></table>")


class AppGrafica:
    """Interfaz gráfica para Colab con ipywidgets. Solo habla con el Gestor y
    el almacén (como la consola): no contiene lógica de negocio. Cada acción
    captura los errores de validación y los muestra en la barra de estado."""

    def __init__(self, gestor, ruta):
        self.gestor = gestor
        self.ruta = ruta
        self.mensaje = widgets.HTML()
        self.pendientes_aviso = widgets.HTML()
        self._construir()
        self.refrescar()

    # ---------- Utilidades ----------

    def _hoy(self):
        return self.gestor.reloj()

    def _avisar(self, texto, error=False):
        color = "#b00020" if error else "#1b5e20"
        self.mensaje.value = (f"<span style='color:{color}'>"
                              f"{html.escape(texto)}</span>")

    def _ejecutar(self, accion, guardar=True):
        """Corre la acción; si devuelve un texto, lo muestra. Guarda el JSON
        y refresca todas las vistas, también si hubo error."""
        try:
            texto = accion()
            if guardar:
                almacen.guardar(self.gestor, self.ruta)
            self._avisar(texto or "Listo")
        except ValueError as error:
            self._avisar(str(error), error=True)
        except OSError as error:
            self._avisar(f"No se pudo guardar el archivo: {error}", error=True)
        finally:
            self.refrescar()

    def _boton(self, texto, accion, guardar=True, estilo=""):
        boton = widgets.Button(description=texto, button_style=estilo)
        boton.on_click(lambda _: self._ejecutar(accion, guardar))
        return boton

    @staticmethod
    def _fecha_obligatoria(valor, nombre="la fecha"):
        if valor is None:
            raise ValueError(f"Elige {nombre}")
        return valor

    # ---------- Construcción ----------

    def _construir(self):
        self.boton_deshacer = self._boton("↩ Deshacer", self._deshacer)
        barra = widgets.HBox([self.boton_deshacer, self.mensaje])
        self.pestanas = widgets.Tab(children=[
            self._pestana_registrar(), self._pestana_bitacora(),
            self._pestana_meses(), self._pestana_recurrentes(),
            self._pestana_categorias()])
        for i, titulo in enumerate(("Registrar", "Bitácora", "Meses",
                                    "Recurrentes", "Categorías")):
            self.pestanas.set_title(i, titulo)
        titulo = widgets.HTML("<h3>Gestor de Gastos</h3>")
        self.contenedor = widgets.VBox(
            [titulo, self.pendientes_aviso, barra, self.pestanas])

    def mostrar(self):
        """Muestra la aplicación en el cuaderno."""
        from IPython.display import display
        display(self.contenedor)

    # ---------- Registrar ----------

    def _pestana_registrar(self):
        self.reg_monto = widgets.Text(description="Monto COP", placeholder="25000")
        self.reg_fecha = widgets.DatePicker(description="Fecha", value=self._hoy())
        self.reg_categoria = widgets.Dropdown(description="Categoría")
        self.reg_descripcion = widgets.Text(description="Descripción")
        self.reg_boton = self._boton("Registrar", self._registrar, estilo="success")
        return widgets.VBox([self.reg_monto, self.reg_fecha, self.reg_categoria,
                             self.reg_descripcion, self.reg_boton])

    def _registrar(self):
        gasto = self.gestor.gastos.registrar(
            leer_monto(self.reg_monto.value),
            self._fecha_obligatoria(self.reg_fecha.value),
            self.reg_categoria.value or "",
            self.reg_descripcion.value)
        self.reg_monto.value = ""
        self.reg_descripcion.value = ""
        return f"Registrado el gasto #{gasto.id} por {formatear_monto(gasto.monto)}"

    def _deshacer(self):
        resultado = self.gestor.deshacer()
        if resultado is None:
            return "No hay nada que deshacer"
        operacion, gasto = resultado
        return f"Deshecho ({operacion}) el gasto #{gasto.id}"

    # ---------- Bitácora ----------

    def _pestana_bitacora(self):
        self.fil_texto = widgets.Text(description="Descripción")
        self.fil_categoria = widgets.Dropdown(description="Categoría")
        self.fil_desde = widgets.DatePicker(description="Desde")
        self.fil_hasta = widgets.DatePicker(description="Hasta")
        self.fil_boton = self._boton("Filtrar", lambda: "Filtros aplicados",
                                     guardar=False)
        self.fil_limpiar = self._boton("Limpiar", self._limpiar_filtros,
                                       guardar=False)
        self.tabla = widgets.HTML()
        self.ed_id = widgets.BoundedIntText(description="Id gasto", min=1,
                                            max=10 ** 9, value=1)
        self.ed_monto = widgets.Text(description="Monto",
                                     placeholder="(sin cambio)")
        self.ed_fecha = widgets.DatePicker(description="Fecha")
        self.ed_categoria = widgets.Dropdown(description="Categoría")
        self.ed_descripcion = widgets.Text(description="Descripción",
                                           placeholder="(sin cambio)")
        self.ed_editar = self._boton("Editar", self._editar)
        self.ed_borrar = self._boton("Borrar", self._borrar, estilo="danger")
        edicion = widgets.VBox([
            widgets.HTML("<b>Editar o borrar un gasto</b> (deja en blanco lo "
                         "que no quieras cambiar)"),
            self.ed_id, self.ed_monto, self.ed_fecha, self.ed_categoria,
            self.ed_descripcion, widgets.HBox([self.ed_editar, self.ed_borrar])])
        filtros = widgets.VBox([
            self.fil_texto, self.fil_categoria,
            widgets.HBox([self.fil_desde, self.fil_hasta]),
            widgets.HBox([self.fil_boton, self.fil_limpiar])])
        return widgets.VBox([filtros, self.tabla, edicion])

    def _limpiar_filtros(self):
        self.fil_texto.value = ""
        self.fil_categoria.value = TODAS
        self.fil_desde.value = None
        self.fil_hasta.value = None
        return "Filtros limpiados"

    def gastos_filtrados(self):
        """Gastos que cumplen los filtros de la pestaña Bitácora. O(n)."""
        servicio = self.gestor.gastos
        desde, hasta = self.fil_desde.value, self.fil_hasta.value
        if desde or hasta:
            gastos = servicio.consultar_rango(desde or date.min, hasta or date.max)
        else:
            gastos = servicio.bitacora()
        if self.fil_texto.value.strip():
            ids = {g.id for g in
                   servicio.buscar_por_descripcion(self.fil_texto.value)}
            gastos = [g for g in gastos if g.id in ids]
        if self.fil_categoria.value not in (None, TODAS):
            ids = {g.id for g in
                   servicio.filtrar_por_categoria(self.fil_categoria.value)}
            gastos = [g for g in gastos if g.id in ids]
        return gastos

    def _editar(self):
        id_gasto = self.ed_id.value
        monto = self.ed_monto.value.strip()
        categoria = self.ed_categoria.value
        gasto = self.gestor.gastos.editar(
            id_gasto,
            monto=leer_monto(monto) if monto else None,
            fecha=self.ed_fecha.value,
            categoria=None if categoria in (None, SIN_CAMBIO) else categoria,
            descripcion=self.ed_descripcion.value.strip() or None)
        self.ed_monto.value = ""
        self.ed_descripcion.value = ""
        self.ed_fecha.value = None
        return f"Actualizado el gasto #{gasto.id}"

    def _borrar(self):
        gasto = self.gestor.borrar_gasto(self.ed_id.value)
        return f"Borrado el gasto #{gasto.id} (puedes deshacerlo)"

    # ---------- Meses ----------

    def _pestana_meses(self):
        self.mes_vista = widgets.HTML()
        self.mes_anterior = self._boton("◀ Mes anterior", self._mes_anterior,
                                        guardar=False)
        self.mes_siguiente = self._boton("Mes siguiente ▶", self._mes_siguiente,
                                         guardar=False)
        return widgets.VBox([widgets.HBox([self.mes_anterior, self.mes_siguiente]),
                             self.mes_vista])

    def _mes_anterior(self):
        if not self.gestor.gastos.meses.anterior():
            return "Ya estás en el primer mes"

    def _mes_siguiente(self):
        if not self.gestor.gastos.meses.siguiente():
            return "Ya estás en el último mes"

    # ---------- Recurrentes ----------

    def _pestana_recurrentes(self):
        self.rec_monto = widgets.Text(description="Monto mensual")
        self.rec_categoria = widgets.Dropdown(description="Categoría")
        self.rec_descripcion = widgets.Text(description="Descripción")
        self.rec_dia = widgets.BoundedIntText(description="Día del mes",
                                              min=1, max=31, value=1)
        self.rec_nota = widgets.Text(description="Nota")
        self.rec_agregar = self._boton("Añadir recurrente", self._rec_agregar,
                                       estilo="success")
        self.rec_lista = widgets.HTML()
        self.pag_recurrente = widgets.Dropdown(description="Pagar")
        self.pag_monto = widgets.Text(description="Monto",
                                      placeholder="(el de la plantilla)")
        self.pag_fecha = widgets.DatePicker(description="Fecha",
                                            value=self._hoy())
        self.pag_boton = self._boton("Pagar", self._rec_pagar, estilo="success")
        self.ter_recurrente = widgets.Dropdown(description="Terminar")
        self.ter_boton = self._boton("Terminar", self._rec_terminar,
                                     estilo="warning")
        return widgets.VBox([
            widgets.HTML("<b>Nuevo recurrente</b>"), self.rec_monto,
            self.rec_categoria, self.rec_descripcion, self.rec_dia,
            self.rec_nota, self.rec_agregar, self.rec_lista,
            widgets.HTML("<b>Pagar un pendiente del mes</b>"),
            self.pag_recurrente, self.pag_monto, self.pag_fecha, self.pag_boton,
            widgets.HTML("<b>Terminar un recurrente</b>"),
            widgets.HBox([self.ter_recurrente, self.ter_boton])])

    def _rec_agregar(self):
        r = self.gestor.recurrentes.agregar(
            leer_monto(self.rec_monto.value), self.rec_categoria.value or "",
            self.rec_descripcion.value, self.rec_dia.value, self.rec_nota.value)
        self.rec_monto.value = ""
        self.rec_descripcion.value = ""
        self.rec_nota.value = ""
        return f"Recurrente #{r.id} creado"

    def _rec_pagar(self):
        if self.pag_recurrente.value is None:
            raise ValueError("No hay pendientes para pagar")
        texto = self.pag_monto.value.strip()
        gasto = self.gestor.recurrentes.pagar(
            self.pag_recurrente.value,
            monto=leer_monto(texto) if texto else None,
            fecha=self._fecha_obligatoria(self.pag_fecha.value))
        self.pag_monto.value = ""
        return f"Pago registrado: gasto #{gasto.id} por {formatear_monto(gasto.monto)}"

    def _rec_terminar(self):
        if self.ter_recurrente.value is None:
            raise ValueError("No hay recurrentes activos")
        r = self.gestor.recurrentes.terminar(self.ter_recurrente.value)
        return f"Recurrente #{r.id} terminado"

    # ---------- Categorías ----------

    def _pestana_categorias(self):
        self.cat_lista = widgets.HTML()
        self.cat_nombre = widgets.Text(description="Nueva")
        self.cat_crear = self._boton("Crear categoría", self._cat_crear,
                                     estilo="success")
        self.cat_eliminar_sel = widgets.Dropdown(description="Eliminar")
        self.cat_eliminar = self._boton("Eliminar", self._cat_eliminar,
                                        estilo="danger")
        return widgets.VBox([
            self.cat_lista, self.cat_nombre, self.cat_crear,
            widgets.HTML("Al eliminar una categoría, sus gastos y recurrentes "
                         "pasan a <b>Otros</b>. No se puede deshacer."),
            widgets.HBox([self.cat_eliminar_sel, self.cat_eliminar])])

    def _cat_crear(self):
        nombre = self.gestor.gastos.agregar_categoria(self.cat_nombre.value)
        self.cat_nombre.value = ""
        return f"Categoría '{nombre}' creada"

    def _cat_eliminar(self):
        if self.cat_eliminar_sel.value is None:
            raise ValueError("No hay categorías que se puedan eliminar")
        nombre = self.cat_eliminar_sel.value
        movidos = self.gestor.eliminar_categoria(nombre)
        return f"Categoría '{nombre}' eliminada; {movidos} gasto(s) pasaron a Otros"

    # ---------- Refresco ----------

    def refrescar(self):
        """Vuelve a leer el estado y actualiza todas las vistas."""
        categorias = self.gestor.gastos.categorias()
        for desplegable in (self.reg_categoria, self.rec_categoria):
            _poner_opciones(desplegable, categorias)
        _poner_opciones(self.fil_categoria, [TODAS] + categorias)
        _poner_opciones(self.ed_categoria, [SIN_CAMBIO] + categorias)
        self._refrescar_bitacora()
        self._refrescar_meses()
        self._refrescar_recurrentes()
        self._refrescar_categorias(categorias)
        self.boton_deshacer.disabled = not self.gestor.gastos.hay_que_deshacer()

    def _refrescar_bitacora(self):
        try:
            self.tabla.value = tabla_html(self.gastos_filtrados(),
                                          "No hay gastos con esos filtros.")
        except ValueError as error:
            self.tabla.value = f"<p style='color:#b00020'>{html.escape(str(error))}</p>"

    def _refrescar_meses(self):
        nav = self.gestor.gastos.meses
        self.mes_vista.value = (
            f"<h4>{nav.mes_actual()} — total {formatear_monto(nav.total_actual())}"
            f"</h4>" + tabla_html(nav.gastos_actual(), "Sin gastos este mes."))
        self.mes_anterior.disabled = not nav.hay_anterior()
        self.mes_siguiente.disabled = not nav.hay_siguiente()

    def _refrescar_recurrentes(self):
        servicio = self.gestor.recurrentes
        activos = servicio.listar_activos()
        pendientes = servicio.pendientes()
        self.rec_lista.value = self._lista_recurrentes(activos)
        _poner_opciones(self.pag_recurrente, [
            (f"#{r.id} día {r.dia}: {r.descripcion}", r.id) for r in pendientes])
        _poner_opciones(self.ter_recurrente, [
            (f"#{r.id} {r.descripcion}", r.id) for r in activos])
        self.pendientes_aviso.value = self._aviso_pendientes(pendientes)

    @staticmethod
    def _lista_recurrentes(activos):
        if not activos:
            return "<p><i>No hay recurrentes activos.</i></p>"
        items = "".join(
            f"<li>#{r.id} día {r.dia}: {html.escape(r.descripcion)} — "
            f"{formatear_monto(r.monto)} [{html.escape(r.categoria)}] "
            f"{html.escape(r.nota)}</li>" for r in activos)
        return f"<b>Recurrentes activos</b><ul>{items}</ul>"

    @staticmethod
    def _aviso_pendientes(pendientes):
        if not pendientes:
            return ""
        items = "".join(
            f"<li>día {r.dia}: {html.escape(r.descripcion)} "
            f"{formatear_monto(r.monto)} {html.escape(r.nota)}</li>"
            for r in pendientes)
        return (f"<div style='background:#fff8e1;padding:6px'>"
                f"<b>Pendientes de pago este mes</b><ul>{items}</ul></div>")

    def _refrescar_categorias(self, categorias):
        items = "".join(f"<li>{html.escape(n)}</li>" for n in categorias)
        self.cat_lista.value = f"<b>Categorías</b><ul>{items}</ul>"
        eliminables = [n for n in categorias if Categoria(n).es_eliminable]
        _poner_opciones(self.cat_eliminar_sel, eliminables)
