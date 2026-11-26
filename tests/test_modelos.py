import pytest

from exceptions.errores import DatosInvalidosError, StockInsuficienteError
from models.base import ModeloBase
from models.categoria import Categoria
from models.movimiento import Movimiento, crear_movimiento
from models.producto import Producto, ProductoPerecedero
from tests.conftest import dias_desde_hoy, producto


class TestProducto:
    def test_calcula_valor_total_y_reposicion(self):
        p = producto(cantidad=4, precio=12.5, stock_minimo=5)
        assert p.valor_total == 50.0
        assert p.necesita_reposicion is True

    def test_no_necesita_reposicion_sobre_el_minimo(self):
        assert producto(cantidad=6, stock_minimo=5).necesita_reposicion is False

    def test_normaliza_espacios_del_nombre(self):
        assert producto(nombre="  Monitor    24  ").nombre == "Monitor 24"

    @pytest.mark.parametrize("atributo, valor", [
        ("cantidad", -1),
        ("cantidad", "abc"),
        ("precio", -0.01),
        ("precio", "gratis"),
        ("stock_minimo", -3),
        ("estado", 7),
        ("categoria_id", None),
        ("nombre", "<script>"),
        ("nombre", "A"),
    ])
    def test_setter_rechaza_valores_invalidos(self, atributo, valor):
        p = producto()
        anterior = getattr(p, atributo)
        with pytest.raises(DatosInvalidosError):
            setattr(p, atributo, valor)
        assert getattr(p, atributo) == anterior

    def test_setter_convierte_tipos(self):
        p = producto()
        p.cantidad = "8"
        p.precio = "19.90"
        assert (p.cantidad, p.precio) == (8, 19.9)

    def test_atributos_encapsulados(self):
        p = producto(cantidad=3)
        assert p._cantidad == 3
        assert "cantidad" not in vars(p)

    def test_to_dict_expone_campos_calculados(self):
        datos = producto(cantidad=2, precio=10).to_dict()
        assert datos["valor_total"] == 20.0
        assert datos["tipo"] == "General"
        assert "fecha_vencimiento" not in datos


class TestProductoPerecedero:
    def test_hereda_de_producto(self):
        p = producto(fecha_vencimiento=dias_desde_hoy(5))
        assert isinstance(p, ProductoPerecedero)
        assert isinstance(p, Producto)
        assert isinstance(p, ModeloBase)

    def test_polimorfismo_de_tipo_y_to_dict(self):
        general = producto()
        perecedero = producto(fecha_vencimiento=dias_desde_hoy(5))
        assert [p.tipo for p in (general, perecedero)] == ["General", "Perecedero"]
        assert perecedero.to_dict()["esta_vencido"] is False

    def test_detecta_vencimiento(self):
        assert producto(fecha_vencimiento=dias_desde_hoy(-1)).esta_vencido is True

    def test_rechaza_fecha_con_formato_invalido(self):
        p = producto(fecha_vencimiento=dias_desde_hoy(5))
        with pytest.raises(DatosInvalidosError):
            p.fecha_vencimiento = "31/12/2030"


class TestMovimiento:
    def test_entrada_suma_stock_y_calcula_subtotal(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 4, "tipo_movimiento": "entrada",
                              "precio_compra": "2.5"})
        assert m.aplicar_a_stock(10) == 14
        assert (m.stock_anterior, m.stock_nuevo, m.subtotal) == (10, 14, 10.0)

    def test_salida_resta_stock(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 3, "tipo_movimiento": "SALIDA"})
        assert m.aplicar_a_stock(10) == 7
        assert m.subtotal is None

    def test_salida_sin_stock_suficiente(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 11, "tipo_movimiento": "SALIDA"})
        with pytest.raises(StockInsuficienteError):
            m.aplicar_a_stock(10)
        assert m.stock_nuevo is None

    def test_ajuste_fija_el_stock_y_admite_cero(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 0, "tipo_movimiento": "AJUSTE"})
        assert m.aplicar_a_stock(25) == 0

    @pytest.mark.parametrize("datos", [
        {"id_producto": None, "cantidad": 1},
        {"id_producto": 1, "cantidad": 0, "tipo_movimiento": "ENTRADA"},
        {"id_producto": 1, "cantidad": -2, "tipo_movimiento": "AJUSTE"},
        {"id_producto": 1, "cantidad": 1, "tipo_movimiento": "DEVOLUCION"},
    ])
    def test_rechaza_datos_invalidos(self, datos):
        with pytest.raises(DatosInvalidosError):
            crear_movimiento(datos)

    def test_stock_calculado_es_de_solo_lectura(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 1})
        with pytest.raises(AttributeError):
            m.stock_nuevo = 999

    def test_cargar_historial(self):
        m = crear_movimiento({"id_producto": 1, "cantidad": 1})
        m.cargar_historial(5, 6, 12.0)
        assert m.to_dict()["stock_nuevo"] == 6


def test_modelo_base_es_abstracto():
    with pytest.raises(TypeError):
        ModeloBase()


@pytest.mark.parametrize("clase", [Producto, ProductoPerecedero, Movimiento, Categoria])
def test_todos_los_modelos_heredan_de_modelo_base(clase):
    assert issubclass(clase, ModeloBase)
