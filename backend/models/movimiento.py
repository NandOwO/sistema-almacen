from exceptions.errores import DatosInvalidosError, StockInsuficienteError
from models.base import ModeloBase

TIPO_ENTRADA = "ENTRADA"
TIPO_SALIDA = "SALIDA"
TIPO_AJUSTE = "AJUSTE"
TIPOS_VALIDOS = (TIPO_ENTRADA, TIPO_SALIDA, TIPO_AJUSTE)


class Movimiento(ModeloBase):
    """Entrada, salida o ajuste de stock de un producto."""

    def __init__(
        self,
        id,
        id_producto,
        cantidad,
        tipo_movimiento=TIPO_ENTRADA,
        motivo="COMPRA",
        id_proveedor=None,
        numero_documento=None,
        observacion=None,
        precio_compra=None,
        id_usuario=None,
        stock_anterior=None,
        stock_nuevo=None,
        subtotal=None,
        fecha=None,
        producto_nombre=None,
        proveedor_nombre=None,
        usuario_nombre=None,
    ):
        self.id = id
        self.id_producto = id_producto
        self._tipo_movimiento = self._normalizar_tipo(tipo_movimiento)
        self._cantidad = self._normalizar_cantidad(cantidad, self._tipo_movimiento)
        self.motivo = (motivo or "").strip().upper() or "COMPRA"
        self.id_proveedor = id_proveedor
        self.numero_documento = numero_documento
        self.observacion = observacion
        self.precio_compra = precio_compra
        self.id_usuario = id_usuario
        self._stock_anterior = stock_anterior
        self._stock_nuevo = stock_nuevo
        self._subtotal = subtotal
        self.fecha = fecha

        self.producto_nombre = producto_nombre
        self.proveedor_nombre = proveedor_nombre
        self.usuario_nombre = usuario_nombre
        self.validar()

    @staticmethod
    def _normalizar_tipo(tipo):
        tipo = (tipo or TIPO_ENTRADA).upper()
        if tipo not in TIPOS_VALIDOS:
            raise DatosInvalidosError(
                "Tipo de movimiento inválido (use ENTRADA, SALIDA o AJUSTE)."
            )
        return tipo

    @staticmethod
    def _normalizar_cantidad(cantidad, tipo):
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            raise DatosInvalidosError("La cantidad debe ser un número entero.")
        if cantidad < 0:
            raise DatosInvalidosError("La cantidad no puede ser negativa.")
        if tipo != TIPO_AJUSTE and cantidad == 0:
            raise DatosInvalidosError("La cantidad debe ser mayor que cero.")
        return cantidad

    @property
    def tipo_movimiento(self):
        """ENTRADA, SALIDA o AJUSTE."""
        return self._tipo_movimiento

    @property
    def cantidad(self):
        """Unidades del movimiento; en un ajuste, el stock final."""
        return self._cantidad

    @property
    def stock_anterior(self):
        """Stock del producto antes de aplicar el movimiento."""
        return self._stock_anterior

    @property
    def stock_nuevo(self):
        """Stock del producto después de aplicar el movimiento."""
        return self._stock_nuevo

    @property
    def subtotal(self):
        """Precio de compra por cantidad, si se indicó precio."""
        return self._subtotal

    def validar(self):
        """Exige que el movimiento indique un producto."""
        if not self.id_producto:
            raise DatosInvalidosError("Debe seleccionar un producto.")

    def cargar_historial(self, stock_anterior, stock_nuevo, subtotal):
        """Restaura los valores calculados de un movimiento ya registrado."""
        self._stock_anterior = stock_anterior
        self._stock_nuevo = stock_nuevo
        self._subtotal = subtotal

    def aplicar_a_stock(self, stock_anterior):
        """Calcula el stock resultante y el subtotal; impide stock negativo."""
        stock_anterior = int(stock_anterior)
        if self._tipo_movimiento == TIPO_ENTRADA:
            stock_nuevo = stock_anterior + self._cantidad
        elif self._tipo_movimiento == TIPO_SALIDA:
            stock_nuevo = stock_anterior - self._cantidad
            if stock_nuevo < 0:
                raise StockInsuficienteError(
                    f"No hay stock suficiente. Disponible: {stock_anterior}, "
                    f"solicitado: {self.cantidad}."
                )
        else:
            stock_nuevo = self._cantidad

        self._stock_anterior = stock_anterior
        self._stock_nuevo = stock_nuevo
        self._subtotal = self._calcular_subtotal()
        return stock_nuevo

    def _calcular_subtotal(self):
        if self.precio_compra is None:
            return None
        return round(float(self.precio_compra) * self._cantidad, 2)

    def to_dict(self):
        """Representación del movimiento para las respuestas JSON."""
        return {
            "id": self.id,
            "id_producto": self.id_producto,
            "producto": self.producto_nombre,
            "cantidad": self.cantidad,
            "tipo_movimiento": self.tipo_movimiento,
            "motivo": self.motivo,
            "id_proveedor": self.id_proveedor,
            "proveedor": self.proveedor_nombre,
            "numero_documento": self.numero_documento,
            "observacion": self.observacion,
            "precio_compra": (
                float(self.precio_compra) if self.precio_compra is not None else None
            ),
            "subtotal": float(self.subtotal) if self.subtotal is not None else None,
            "stock_anterior": self.stock_anterior,
            "stock_nuevo": self.stock_nuevo,
            "id_usuario": self.id_usuario,
            "usuario": self.usuario_nombre,
            "fecha": (
                self.fecha.isoformat()
                if hasattr(self.fecha, "isoformat")
                else self.fecha
            ),
        }


def crear_movimiento(datos):
    """Construye un movimiento normalizando los datos del formulario."""
    precio = datos.get("precio_compra")
    return Movimiento(
        id=datos.get("id"),
        id_producto=int(datos["id_producto"]) if datos.get("id_producto") else None,
        cantidad=int(datos.get("cantidad", 0)),
        tipo_movimiento=datos.get("tipo_movimiento"),
        motivo=datos.get("motivo"),
        id_proveedor=(
            int(datos["id_proveedor"]) if datos.get("id_proveedor") else None
        ),
        numero_documento=(datos.get("numero_documento") or "").strip() or None,
        observacion=(datos.get("observacion") or "").strip() or None,
        precio_compra=float(precio) if precio not in (None, "", "null") else None,
        id_usuario=datos.get("id_usuario"),
    )
