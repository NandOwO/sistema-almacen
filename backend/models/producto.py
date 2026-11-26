from datetime import date

import validadores
from exceptions.errores import DatosInvalidosError
from models.base import ESTADOS_VALIDOS, ModeloBase


def _entero_no_negativo(valor, mensaje):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise DatosInvalidosError(mensaje)
    if numero < 0:
        raise DatosInvalidosError(mensaje)
    return numero


class Producto(ModeloBase):
    """Producto del catálogo con stock, precio y umbral de reposición."""

    def __init__(
        self,
        id,
        nombre,
        categoria_id,
        cantidad,
        precio,
        stock_minimo=5,
        categoria_nombre=None,
        estado=1,
    ):
        self.id = id
        self.nombre = nombre
        self.categoria_id = categoria_id
        self.categoria_nombre = categoria_nombre
        self.cantidad = cantidad
        self.precio = precio
        self.stock_minimo = stock_minimo
        self.estado = estado

    @property
    def nombre(self):
        """Nombre descriptivo, sin espacios repetidos."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = validadores.texto_general(valor, "Nombre del producto", maximo=120)

    @property
    def categoria_id(self):
        """Id de la categoría a la que pertenece."""
        return self._categoria_id

    @categoria_id.setter
    def categoria_id(self, valor):
        if not valor:
            raise DatosInvalidosError("Debe seleccionar una categoría.")
        self._categoria_id = int(valor)

    @property
    def cantidad(self):
        """Unidades en stock; nunca negativa."""
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor):
        self._cantidad = _entero_no_negativo(valor, "La cantidad no puede ser negativa.")

    @property
    def precio(self):
        """Precio unitario de venta; nunca negativo."""
        return self._precio

    @precio.setter
    def precio(self, valor):
        try:
            precio = float(valor)
        except (TypeError, ValueError):
            raise DatosInvalidosError("El precio debe ser un número.")
        if precio < 0:
            raise DatosInvalidosError("El precio no puede ser negativo.")
        self._precio = precio

    @property
    def stock_minimo(self):
        """Umbral a partir del cual se sugiere reponer."""
        return self._stock_minimo

    @stock_minimo.setter
    def stock_minimo(self, valor):
        self._stock_minimo = _entero_no_negativo(
            valor, "El stock mínimo no puede ser negativo."
        )

    @property
    def estado(self):
        """0 inactivo, 1 activo, 2 eliminado."""
        return self._estado

    @estado.setter
    def estado(self, valor):
        estado = int(valor)
        if estado not in ESTADOS_VALIDOS:
            raise DatosInvalidosError("Estado inválido.")
        self._estado = estado

    @property
    def tipo(self):
        """Tipo de producto; las subclases lo redefinen."""
        return "General"

    @property
    def categoria(self):
        """Nombre de la categoría, si se cargó junto al producto."""
        return self.categoria_nombre

    @property
    def valor_total(self):
        """Cantidad por precio, redondeado a dos decimales."""
        return round(self._cantidad * self._precio, 2)

    @property
    def necesita_reposicion(self):
        """True si el stock está en o bajo el mínimo."""
        return self._cantidad <= self._stock_minimo

    def to_dict(self):
        """Representación del producto para las respuestas JSON."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria_id": self.categoria_id,
            "categoria": self.categoria_nombre,
            "cantidad": self.cantidad,
            "precio": self.precio,
            "stock_minimo": self.stock_minimo,
            "tipo": self.tipo,
            "estado": self.estado,
            "valor_total": self.valor_total,
            "necesita_reposicion": self.necesita_reposicion,
        }


class ProductoPerecedero(Producto):
    """Producto con fecha de vencimiento."""

    def __init__(self, *args, fecha_vencimiento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fecha_vencimiento = fecha_vencimiento

    @property
    def fecha_vencimiento(self):
        """Fecha de vencimiento en formato AAAA-MM-DD."""
        return self._fecha_vencimiento

    @fecha_vencimiento.setter
    def fecha_vencimiento(self, valor):
        self._fecha_vencimiento = validadores.fecha_valida(valor, "Fecha de vencimiento")

    @property
    def tipo(self):
        """Siempre 'Perecedero'."""
        return "Perecedero"

    @property
    def esta_vencido(self):
        """True si la fecha de vencimiento ya pasó."""
        if not self._fecha_vencimiento:
            return False
        return date.fromisoformat(self._fecha_vencimiento) < date.today()

    def to_dict(self):
        """Agrega la fecha de vencimiento y si está vencido."""
        datos = super().to_dict()
        datos["fecha_vencimiento"] = self.fecha_vencimiento
        datos["esta_vencido"] = self.esta_vencido
        return datos
