from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from models.categoria import Categoria
from models.movimiento import crear_movimiento
from patterns.fabrica_producto import crear_producto
from patterns.singleton import Singleton

CARPETA_DATOS = Path(__file__).resolve().parent.parent / "data"
CATEGORIAS = ("Tecnología", "Papelería", "Alimentos", "Limpieza")


def dias_desde_hoy(dias):
    return (date.today() + timedelta(days=dias)).isoformat()


def producto(id=1, nombre="Teclado mecánico", categoria_id=1, categoria="Tecnología",
             cantidad=10, precio=100.0, stock_minimo=5, fecha_vencimiento=None):
    return crear_producto({
        "id": id, "nombre": nombre, "categoria_id": categoria_id, "categoria": categoria,
        "cantidad": cantidad, "precio": precio, "stock_minimo": stock_minimo,
        "fecha_vencimiento": fecha_vencimiento,
    })


def movimiento(id_producto, cantidad, tipo="SALIDA", hace_dias=0, proveedor=None, precio=None):
    mov = crear_movimiento({
        "id_producto": id_producto, "cantidad": cantidad,
        "tipo_movimiento": tipo, "precio_compra": precio,
    })
    mov.fecha = datetime.combine(date.today() - timedelta(days=hace_dias), datetime.min.time())
    mov.proveedor_nombre = proveedor
    if precio is not None:
        mov.aplicar_a_stock(1000)
    return mov


class CategoriaRepoFalso:
    def __init__(self, nombres=CATEGORIAS):
        self.categorias = [Categoria(i, n) for i, n in enumerate(nombres, start=1)]

    def listar(self, solo_activos=False):
        return list(self.categorias)

    def obtener(self, id):
        return next((c for c in self.categorias if c.id == id), None)


class ProductoRepoFalso:
    def __init__(self, productos=()):
        self.productos = list(productos)

    def listar(self, solo_activos=False):
        return [p for p in self.productos if p.estado == 1 or not solo_activos]

    def obtener(self, id):
        return next((p for p in self.productos if p.id == id), None)

    def agregar(self, nuevo):
        nuevo.id = max((p.id for p in self.productos), default=0) + 1
        self.productos.append(nuevo)
        return nuevo

    def actualizar(self, cambiado):
        self.productos = [cambiado if p.id == cambiado.id else p for p in self.productos]
        return cambiado


class ProveedorRepoFalso:
    def __init__(self, ids=(1,)):
        self.ids = set(ids)

    def obtener(self, id):
        return object() if id in self.ids else None


class MovimientoRepoFalso:
    def __init__(self, movimientos=()):
        self.movimientos = list(movimientos)

    def listar(self, limite=100):
        return self.movimientos[:limite]

    def listar_filtrado(self, filtros):
        tipo = filtros.get("tipo_movimiento")
        return [m for m in self.movimientos if not tipo or m.tipo_movimiento == tipo]

    def registrar(self, mov):
        mov.aplicar_a_stock(100)
        self.movimientos.append(mov)
        return mov


@pytest.fixture
def productos_muestra():
    return [
        producto(1, "Laptop 14", 1, "Tecnología", 12, 2500, 5),
        producto(2, "Mouse inalámbrico", 1, "Tecnología", 3, 60, 10),
        producto(3, "Cuaderno A4", 2, "Papelería", 0, 4.5, 30),
        producto(4, "Leche entera", 3, "Alimentos", 40, 5, 15, dias_desde_hoy(-3)),
        producto(5, "Café molido", 3, "Alimentos", 25, 22, 10, dias_desde_hoy(10)),
        producto(6, "Yogurt fresa", 3, "Alimentos", 7, 3.3, 7, dias_desde_hoy(90)),
    ]


@pytest.fixture
def categoria_repo():
    return CategoriaRepoFalso()


@pytest.fixture
def producto_repo():
    return ProductoRepoFalso([producto(1, "Mouse inalámbrico", 1, "Tecnología", 3, 60, 10)])


@pytest.fixture
def singleton_limpio():
    yield
    for clase in list(Singleton._instancias):
        clase.reiniciar()
