import pytest

from exceptions.errores import DatosInvalidosError, ProductoNoEncontradoError, StockInsuficienteError
from seed_data import PRODUCTOS, _datos_producto
from services.inventario_service import InventarioService
from services.movimiento_service import MovimientoService
from tests.conftest import (
    MovimientoRepoFalso, ProductoRepoFalso, ProveedorRepoFalso, dias_desde_hoy, producto,
)


@pytest.fixture
def inventario(producto_repo, categoria_repo):
    return InventarioService(repositorio=producto_repo, categoria_repo=categoria_repo)


class TestInventarioService:
    def test_crea_producto_y_le_asigna_id(self, inventario, producto_repo):
        nuevo = inventario.crear_producto(
            {"nombre": "Monitor 27", "categoria_id": 1, "cantidad": 4, "precio": 900}
        )
        assert nuevo.id == 2
        assert producto_repo.obtener(2).nombre == "Monitor 27"

    def test_rechaza_categoria_inexistente(self, inventario):
        with pytest.raises(DatosInvalidosError, match="categoría"):
            inventario.crear_producto({"nombre": "Monitor 27", "categoria_id": 99})

    def test_rechaza_vencimiento_pasado_al_crear(self, inventario):
        with pytest.raises(DatosInvalidosError, match="fecha pasada"):
            inventario.crear_producto({"nombre": "Yogurt", "categoria_id": 3,
                                       "fecha_vencimiento": dias_desde_hoy(-1)})

    def test_permite_editar_producto_ya_vencido_sin_cambiar_la_fecha(self, categoria_repo):
        vencida = dias_desde_hoy(-10)
        repo = ProductoRepoFalso([producto(1, "Leche entera", 3, "Alimentos", fecha_vencimiento=vencida)])
        servicio = InventarioService(repositorio=repo, categoria_repo=categoria_repo)
        editado = servicio.actualizar_producto(1, {"nombre": "Leche entera 1L", "categoria_id": 3,
                                                   "fecha_vencimiento": vencida})
        assert editado.nombre == "Leche entera 1L"

    def test_obtener_inexistente(self, inventario):
        with pytest.raises(ProductoNoEncontradoError):
            inventario.obtener_producto(404)

    def test_cambiar_a_estado_invalido(self, inventario):
        with pytest.raises(DatosInvalidosError):
            inventario.cambiar_estado_producto(1, 2)


@pytest.fixture
def servicio_movimientos(producto_repo):
    return MovimientoService(repositorio=MovimientoRepoFalso(), producto_repo=producto_repo,
                             proveedor_repo=ProveedorRepoFalso(ids={1}))


ENTRADA_VALIDA = {"id_producto": 1, "cantidad": 5, "tipo_movimiento": "ENTRADA",
                  "id_proveedor": 1, "numero_documento": "F001-123", "precio_compra": 40}


class TestMovimientoService:
    def test_registra_entrada_completa(self, servicio_movimientos):
        mov = servicio_movimientos.registrar_movimiento(ENTRADA_VALIDA, id_usuario=7)
        assert mov.id_usuario == 7
        assert mov.subtotal == 200.0

    @pytest.mark.parametrize("campo, mensaje", [
        ("id_proveedor", "proveedor"),
        ("numero_documento", "documento"),
        ("precio_compra", "precio de compra"),
    ])
    def test_entrada_exige_datos_de_compra(self, servicio_movimientos, campo, mensaje):
        datos = {k: v for k, v in ENTRADA_VALIDA.items() if k != campo}
        with pytest.raises(DatosInvalidosError, match=mensaje):
            servicio_movimientos.registrar_movimiento(datos, id_usuario=1)

    def test_venta_exige_documento(self, servicio_movimientos):
        with pytest.raises(DatosInvalidosError, match="venta"):
            servicio_movimientos.registrar_movimiento(
                {"id_producto": 1, "cantidad": 1, "tipo_movimiento": "SALIDA", "motivo": "venta"}, 1)

    def test_salida_por_merma_no_exige_documento(self, servicio_movimientos):
        mov = servicio_movimientos.registrar_movimiento(
            {"id_producto": 1, "cantidad": 1, "tipo_movimiento": "SALIDA", "motivo": "MERMA"}, 1)
        assert mov.stock_nuevo == 99

    def test_producto_inexistente(self, servicio_movimientos):
        with pytest.raises(ProductoNoEncontradoError):
            servicio_movimientos.registrar_movimiento(dict(ENTRADA_VALIDA, id_producto=50), 1)

    def test_proveedor_inexistente(self, servicio_movimientos):
        with pytest.raises(DatosInvalidosError, match="proveedor"):
            servicio_movimientos.registrar_movimiento(dict(ENTRADA_VALIDA, id_proveedor=9), 1)

    def test_salida_mayor_al_stock(self, servicio_movimientos):
        with pytest.raises(StockInsuficienteError):
            servicio_movimientos.registrar_movimiento(
                {"id_producto": 1, "cantidad": 500, "tipo_movimiento": "SALIDA", "motivo": "MERMA"}, 1)


def test_los_productos_de_ejemplo_pasan_las_validaciones(categoria_repo):
    repo = ProductoRepoFalso()
    servicio = InventarioService(repositorio=repo, categoria_repo=categoria_repo)
    ids = {c.nombre: c.id for c in categoria_repo.listar()}
    for fila in PRODUCTOS:
        datos = _datos_producto(*fila)
        datos["categoria_id"] = ids[datos.pop("categoria")]
        servicio.crear_producto(datos)
    assert len(repo.productos) == len(PRODUCTOS)
    assert sum(p.tipo == "Perecedero" for p in repo.productos) == 2
