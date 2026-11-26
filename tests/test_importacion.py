import io
import json

import pandas as pd
import pytest

from exceptions.errores import DatosInvalidosError
from services.importacion_service import ImportacionService, LIMITE_FILAS
from services.inventario_service import InventarioService
from tests.conftest import CARPETA_DATOS

ENCABEZADO = "nombre,categoria,cantidad,precio,stock_minimo,fecha_vencimiento\n"


@pytest.fixture
def importacion(producto_repo, categoria_repo):
    inventario = InventarioService(repositorio=producto_repo, categoria_repo=categoria_repo)
    return ImportacionService(inventario=inventario, categoria_repo=categoria_repo)


def csv(filas):
    return io.BytesIO((ENCABEZADO + filas).encode("utf-8"))


class TestArchivosDeEjemplo:
    @pytest.mark.parametrize("archivo, esperados", [
        ("productos_ejemplo.csv", 15),
        ("productos_ejemplo.json", 7),
    ])
    def test_importa_todos_los_validos(self, importacion, producto_repo, archivo, esperados):
        with open(CARPETA_DATOS / archivo, "rb") as contenido:
            resultado = importacion.importar_productos(contenido, archivo)
        assert (resultado["importados"], resultado["rechazados"]) == (esperados, 0)
        assert len(producto_repo.productos) == esperados + 1

    def test_reporta_cada_fila_rechazada(self, importacion):
        with open(CARPETA_DATOS / "productos_con_errores.csv", "rb") as contenido:
            resultado = importacion.importar_productos(contenido, "productos_con_errores.csv")
        assert resultado["importados"] == 2
        assert [e["fila"] for e in resultado["errores"]] == [3, 4, 5, 6, 7, 8, 9, 11]
        motivos = {e["fila"]: e["error"] for e in resultado["errores"]}
        assert motivos[7] == "La categoría 'Iluminación' no existe."
        assert motivos[8] == "Producto repetido dentro del archivo."
        assert motivos[11] == "Ya existe un producto con ese nombre."
        json.dumps(resultado)

    def test_crea_perecederos_y_aplica_stock_minimo_por_defecto(self, importacion, producto_repo):
        with open(CARPETA_DATOS / "productos_ejemplo.json", "rb") as contenido:
            importacion.importar_productos(contenido, "productos_ejemplo.json")
        por_nombre = {p.nombre: p for p in producto_repo.productos}
        assert por_nombre["Queso fresco 500g"].tipo == "Perecedero"
        assert por_nombre["Regla de 30cm"].stock_minimo == 5


class TestLimpieza:
    def test_normaliza_columnas_espacios_y_numeros(self, importacion):
        df = pd.DataFrame({" Nombre ": ["  Cinta   adhesiva "], "CATEGORIA": ["Papelería"],
                           "cantidad": ["12"], "precio": ["3.456"]})
        validos, errores = importacion.limpiar(df)
        fila = validos.iloc[0]
        assert errores == []
        assert (fila["nombre"], fila["cantidad"], fila["precio"], fila["stock_minimo"]) == \
            ("Cinta adhesiva", 12, 3.46, 5)

    def test_la_categoria_no_distingue_mayusculas(self, importacion, producto_repo):
        resultado = importacion.importar_productos(csv("Cinta adhesiva,PAPELERÍA,4,2,,\n"), "x.csv")
        assert resultado["importados"] == 1

    def test_detecta_duplicados_sin_distinguir_mayusculas(self, importacion):
        resultado = importacion.importar_productos(
            csv("Cinta adhesiva,Papelería,4,2,,\nCINTA ADHESIVA,Papelería,1,2,,\n"), "x.csv")
        assert resultado["errores"] == [{"fila": 3, "error": "Producto repetido dentro del archivo."}]

    def test_faltan_columnas_obligatorias(self, importacion):
        with pytest.raises(DatosInvalidosError, match="categoria, cantidad"):
            importacion.limpiar(pd.DataFrame({"nombre": ["A"], "precio": [1]}))

    def test_json_numera_filas_desde_uno(self, importacion):
        contenido = io.BytesIO(json.dumps([
            {"nombre": "Cinta adhesiva", "categoria": "Papelería", "cantidad": -1, "precio": 2},
        ]).encode())
        resultado = importacion.importar_productos(contenido, "x.json")
        assert resultado["errores"][0]["fila"] == 1


class TestLecturaDeArchivos:
    @pytest.mark.parametrize("contenido, nombre, mensaje", [
        (b"a,b", "productos.xlsx", "Formato no soportado"),
        (b"", "productos.csv", "vacío"),
        (b"{no es json", "productos.json", "formato válido"),
        (b'{"nombre": "A"}', "productos.json", "formato válido"),
        ("nombre,categoria,cantidad,precio\nCafé,Alimentos,1,1\n".encode("latin-1"), "p.csv", "UTF-8"),
        (ENCABEZADO.encode(), "productos.csv", "no contiene filas"),
    ])
    def test_errores_de_lectura_cierran_el_archivo(self, importacion, contenido, nombre, mensaje):
        archivo = io.BytesIO(contenido)
        with pytest.raises(DatosInvalidosError, match=mensaje):
            importacion.importar_productos(archivo, nombre)
        assert archivo.closed

    def test_lectura_exitosa_tambien_cierra_el_archivo(self, importacion):
        archivo = csv("Cinta adhesiva,Papelería,4,2,,\n")
        importacion.leer_archivo(archivo, "x.csv")
        assert archivo.closed

    def test_limite_de_filas(self, importacion):
        filas = "".join(f"Producto {i},Papelería,1,1,,\n" for i in range(LIMITE_FILAS + 1))
        with pytest.raises(DatosInvalidosError, match="máximo"):
            importacion.importar_productos(csv(filas), "x.csv")
