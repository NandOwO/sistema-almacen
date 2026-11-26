import pytest

import validadores as val
from exceptions.errores import DatosInvalidosError
from tests.conftest import dias_desde_hoy


@pytest.mark.parametrize("valor, esperado", [
    ("  Arroz   integral ", "Arroz integral"),
    ("Laptop 14''", "Laptop 14''"),
])
def test_texto_general_valido(valor, esperado):
    assert val.texto_general(valor, "Nombre") == esperado


@pytest.mark.parametrize("valor", ["", "   ", "A", "x" * 151, "Precio $10", "<b>Hola</b>"])
def test_texto_general_invalido(valor):
    with pytest.raises(DatosInvalidosError):
        val.texto_general(valor, "Nombre")


def test_ruc_valido():
    assert val.ruc_valido("20100070970") == "20100070970"


@pytest.mark.parametrize("valor, mensaje", [
    ("2010007097", "11 dígitos"),
    ("2010007097A", "11 dígitos"),
    ("30100070970", "empezar con"),
    ("20100070971", "verificador"),
])
def test_ruc_invalido(valor, mensaje):
    with pytest.raises(DatosInvalidosError, match=mensaje):
        val.ruc_valido(valor)


def test_ruc_opcional_y_obligatorio():
    assert val.ruc_valido("") is None
    with pytest.raises(DatosInvalidosError):
        val.ruc_valido("", obligatorio=True)


@pytest.mark.parametrize("funcion, valido, invalido", [
    (val.correo_valido, "ventas@empresa.pe", "ventas@empresa"),
    (val.telefono_valido, "987654321", "98765"),
    (val.usuario_valido, "j.perez_01", "j perez"),
])
def test_formatos(funcion, valido, invalido):
    assert funcion(valido) == valido
    with pytest.raises(DatosInvalidosError):
        funcion(invalido)


@pytest.mark.parametrize("valor, esperado", [
    (None, None),
    ("", None),
    ("2030-01-31", "2030-01-31"),
])
def test_fecha_valida(valor, esperado):
    assert val.fecha_valida(valor) == esperado


@pytest.mark.parametrize("valor", ["31/01/2030", "2030-02-30", "1990-01-01"])
def test_fecha_invalida(valor):
    with pytest.raises(DatosInvalidosError):
        val.fecha_valida(valor)


def test_fecha_no_pasada():
    assert val.fecha_no_pasada(dias_desde_hoy(0)) == dias_desde_hoy(0)
    with pytest.raises(DatosInvalidosError, match="pasada"):
        val.fecha_no_pasada(dias_desde_hoy(-1))
