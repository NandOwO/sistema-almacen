import io
import json

import pytest

import app as aplicacion
from repositories.modulo_repository import ModuloRepository
from routes import producto_routes, reporte_routes
from services.importacion_service import ImportacionService
from services.inventario_service import InventarioService
from tests.conftest import CARPETA_DATOS, CategoriaRepoFalso, ProductoRepoFalso


@pytest.fixture
def cliente(monkeypatch, productos_muestra):
    monkeypatch.setattr(aplicacion, "sembrar_datos_si_vacio", lambda: None)
    monkeypatch.setattr(ModuloRepository, "rutas_de_perfil", lambda self, perfil: ["productos", "reportes"])

    inventario = InventarioService(repositorio=ProductoRepoFalso(productos_muestra),
                                   categoria_repo=CategoriaRepoFalso())
    controlador = producto_routes.controller
    monkeypatch.setattr(controlador, "service", inventario)
    monkeypatch.setattr(controlador, "importacion",
                        ImportacionService(inventario=inventario, categoria_repo=CategoriaRepoFalso()))
    monkeypatch.setattr(reporte_routes.controller, "inventario", inventario)

    return aplicacion.crear_app().test_client()


@pytest.fixture
def sesion(cliente):
    with cliente.session_transaction() as datos:
        datos["id_usuario"] = 1
        datos["id_perfil"] = 1
    return cliente


def test_exige_iniciar_sesion(cliente):
    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 401
    assert "iniciar sesión" in respuesta.get_json()["error"]


def test_ruta_inexistente_responde_404_en_json(cliente):
    respuesta = cliente.get("/api/no-existe")
    assert respuesta.status_code == 404
    assert "error" in respuesta.get_json()


def test_lista_productos(sesion):
    respuesta = sesion.get("/api/productos")
    assert respuesta.status_code == 200
    assert len(respuesta.get_json()) == 6


def test_crear_producto_invalido_responde_400(sesion):
    respuesta = sesion.post("/api/productos", json={"nombre": "Silla", "categoria_id": 1, "cantidad": -1})
    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == "La cantidad no puede ser negativa."


def test_importar_csv(sesion):
    with open(CARPETA_DATOS / "productos_ejemplo.csv", "rb") as archivo:
        respuesta = sesion.post("/api/productos/importar",
                                data={"archivo": (archivo, "productos_ejemplo.csv")},
                                content_type="multipart/form-data")
    assert respuesta.status_code == 201
    assert respuesta.get_json()["importados"] == 15


def test_importar_sin_archivo(sesion):
    respuesta = sesion.post("/api/productos/importar", data={}, content_type="multipart/form-data")
    assert respuesta.status_code == 400


def test_importar_archivo_demasiado_grande(sesion):
    grande = io.BytesIO(b"x" * (3 * 1024 * 1024))
    respuesta = sesion.post("/api/productos/importar", data={"archivo": (grande, "g.csv")},
                            content_type="multipart/form-data")
    assert respuesta.status_code == 413
    assert "2 MB" in respuesta.get_json()["error"]


@pytest.mark.parametrize("formato, tipo_mime", [
    ("excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("pdf", "application/pdf"),
    ("csv", "text/csv"),
    ("json", "application/json"),
])
def test_exportar_reporte(sesion, formato, tipo_mime):
    respuesta = sesion.get(f"/api/reportes/exportar/valorizado?formato={formato}")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == tipo_mime
    assert "attachment" in respuesta.headers["Content-Disposition"]


def test_exportar_json_contiene_los_datos(sesion):
    documento = json.loads(sesion.get("/api/reportes/exportar/bajo-stock?formato=json").data)
    nombres = [f["Producto"] for f in documento["tablas"]["Productos bajo stock"]]
    assert nombres == ["Mouse inalámbrico", "Cuaderno A4", "Yogurt fresa"]


def test_exportar_formato_invalido(sesion):
    respuesta = sesion.get("/api/reportes/exportar/valorizado?formato=docx")
    assert respuesta.status_code == 400
    assert "Formato inválido" in respuesta.get_json()["error"]


def test_reporte_vencimientos(sesion):
    datos = sesion.get("/api/reportes/vencimientos?dias=30").get_json()
    assert datos["resumen"]["vencidos"] == 1
