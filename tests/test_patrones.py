import io
import json
import threading

import pandas as pd
import pytest
from openpyxl import load_workbook

from exceptions.errores import DatosInvalidosError
from models.producto import Producto, ProductoPerecedero
from patterns.estrategias_exportacion import (
    EstrategiaExportacion, ExportacionCSV, ExportacionExcel, ExportacionJSON, ExportacionPDF,
)
from patterns.fabrica_producto import (
    FabricaProducto, FabricaProductoGeneral, FabricaProductoPerecedero,
    crear_producto, obtener_fabrica,
)
from patterns.singleton import Singleton
from repositories import database
from repositories.database import ConexionBD
from services.exportacion_service import ExportacionService
from tests.conftest import dias_desde_hoy

DATOS_BASE = {"nombre": "Lapicero rojo", "categoria_id": 2, "cantidad": 5, "precio": 1.5}


class TestFactoryMethod:
    def test_creador_es_abstracto(self):
        with pytest.raises(TypeError):
            FabricaProducto()

    @pytest.mark.parametrize("fecha, fabrica, clase", [
        (None, FabricaProductoGeneral, Producto),
        ("", FabricaProductoGeneral, Producto),
        ("2030-05-01", FabricaProductoPerecedero, ProductoPerecedero),
    ])
    def test_elige_la_fabrica_segun_los_datos(self, fecha, fabrica, clase):
        datos = dict(DATOS_BASE, fecha_vencimiento=fecha)
        assert isinstance(obtener_fabrica(datos), fabrica)
        assert type(crear_producto(datos)) is clase

    def test_cada_fabrica_concreta_crea_su_producto(self):
        datos = dict(DATOS_BASE, fecha_vencimiento=dias_desde_hoy(30))
        assert type(FabricaProductoGeneral().construir(DATOS_BASE)) is Producto
        assert type(FabricaProductoPerecedero().construir(datos)) is ProductoPerecedero

    def test_aplica_valores_por_defecto(self):
        p = crear_producto({"nombre": "Grapas", "categoria_id": 2})
        assert (p.cantidad, p.precio, p.stock_minimo, p.estado) == (0, 0.0, 5, 1)

    def test_propaga_fecha_invalida(self):
        with pytest.raises(DatosInvalidosError):
            crear_producto(dict(DATOS_BASE, fecha_vencimiento="mañana"))


@pytest.fixture
def tablas():
    detalle = pd.DataFrame({
        "Producto": ["Café molido", "Lápiz"],
        "Stock": [12, 3],
        "Días": pd.array([pd.NA, 4], dtype="Int64"),
        "Valor": [22.5, None],
    })
    resumen = pd.DataFrame({"Categoría": ["Alimentos"], "Total": [100.0]})
    return [("Detalle", detalle), ("Resumen", resumen)]


class TestStrategy:
    def test_estrategia_es_abstracta(self):
        with pytest.raises(TypeError):
            EstrategiaExportacion()

    def test_contexto_registra_los_cuatro_formatos(self):
        assert ExportacionService().formatos == ("excel", "pdf", "csv", "json")

    @pytest.mark.parametrize("formato, extension, tipo_mime", [
        ("excel", "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("pdf", "pdf", "application/pdf"),
        ("csv", "csv", "text/csv"),
        ("json", "json", "application/json"),
    ])
    def test_contexto_delega_en_la_estrategia(self, tablas, formato, extension, tipo_mime):
        archivo = ExportacionService().exportar(formato, "reporte", "Título", tablas)
        assert archivo.nombre == f"reporte.{extension}"
        assert archivo.tipo_mime == tipo_mime
        assert len(archivo.contenido.getvalue()) > 0

    def test_formato_desconocido(self):
        with pytest.raises(DatosInvalidosError, match="Formato inválido"):
            ExportacionService().exportar("docx", "reporte", "Título", [])

    def test_estrategias_intercambiables(self, tablas):
        class EstrategiaTexto(EstrategiaExportacion):
            extension = "txt"
            tipo_mime = "text/plain"

            def exportar(self, titulo, tablas):
                return io.BytesIO(titulo.encode())

        archivo = ExportacionService({"txt": EstrategiaTexto()}).exportar("txt", "r", "Hola", tablas)
        assert archivo.contenido.getvalue() == b"Hola"

    def test_excel_tiene_una_hoja_por_tabla(self, tablas):
        libro = load_workbook(ExportacionExcel().exportar("T", tablas))
        assert libro.sheetnames == ["Detalle", "Resumen"]
        assert libro["Detalle"]["A2"].value == "Café molido"

    def test_pdf_es_valido(self, tablas):
        assert ExportacionPDF().exportar("T", tablas).getvalue().startswith(b"%PDF")

    def test_pdf_admite_tabla_vacia(self):
        assert ExportacionPDF().exportar("T", [("Vacía", pd.DataFrame())]).getvalue()

    def test_csv_separa_secciones_y_conserva_tildes(self, tablas):
        texto = ExportacionCSV().exportar("T", tablas).getvalue().decode("utf-8-sig")
        assert texto.splitlines() == [
            "# Detalle", "Producto,Stock,Días,Valor", "Café molido,12,,22.5", "Lápiz,3,4,",
            "", "# Resumen", "Categoría,Total", "Alimentos,100.0",
        ]

    def test_json_convierte_vacios_en_null(self, tablas):
        documento = json.loads(ExportacionJSON().exportar("Reporte", tablas).getvalue())
        assert documento["titulo"] == "Reporte"
        assert documento["tablas"]["Detalle"][0] == {
            "Producto": "Café molido", "Stock": 12, "Días": None, "Valor": 22.5,
        }


class ConexionFalsa:
    def __init__(self, conectada=True):
        self.conectada = conectada
        self.reconexiones = 0

    def is_connected(self):
        return self.conectada

    def reconnect(self, attempts, delay):
        self.reconexiones += 1
        self.conectada = True


class PoolFalso:
    creados = 0

    def __init__(self, **configuracion):
        PoolFalso.creados += 1
        self.configuracion = configuracion
        self.conexion = ConexionFalsa(conectada=False)

    def get_connection(self):
        return self.conexion


@pytest.mark.usefixtures("singleton_limpio")
class TestSingleton:
    def test_devuelve_siempre_la_misma_instancia(self):
        assert ConexionBD() is ConexionBD()

    def test_instancia_unica_entre_hilos(self):
        instancias = []
        hilos = [threading.Thread(target=lambda: instancias.append(ConexionBD())) for _ in range(20)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        assert len({id(i) for i in instancias}) == 1

    def test_reiniciar_crea_una_nueva_instancia(self):
        primera = ConexionBD()
        ConexionBD.reiniciar()
        assert ConexionBD() is not primera

    def test_instancias_separadas_por_clase(self):
        class Configuracion(metaclass=Singleton):
            pass

        assert Configuracion() is Configuracion()
        assert Configuracion() is not ConexionBD()

    def test_crea_el_pool_una_sola_vez_y_reconecta(self, monkeypatch):
        PoolFalso.creados = 0
        monkeypatch.setattr(database.pooling, "MySQLConnectionPool", PoolFalso)
        primera = database.get_connection()
        segunda = database.get_connection()
        assert PoolFalso.creados == 1
        assert primera is segunda
        assert primera.reconexiones == 1
