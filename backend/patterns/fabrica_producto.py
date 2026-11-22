from abc import ABC, abstractmethod

import validadores
from models.producto import Producto, ProductoPerecedero


class FabricaProducto(ABC):
    """Creador del patrón Factory Method para los productos del catálogo."""

    def construir(self, datos):
        """Normaliza los datos comunes y delega la instancia al método fábrica."""
        return self.crear(self._atributos_comunes(datos), datos)

    @abstractmethod
    def crear(self, atributos, datos):
        """Método fábrica: cada subclase decide qué producto concreto instanciar."""

    @staticmethod
    def _atributos_comunes(datos):
        return {
            "id": datos.get("id"),
            "nombre": datos.get("nombre"),
            "categoria_id": datos.get("categoria_id") or None,
            "categoria_nombre": datos.get("categoria") or datos.get("categoria_nombre"),
            "cantidad": datos.get("cantidad", 0),
            "precio": datos.get("precio", 0),
            "stock_minimo": datos.get("stock_minimo", 5),
            "estado": datos.get("estado", 1),
        }


class FabricaProductoGeneral(FabricaProducto):
    def crear(self, atributos, datos):
        return Producto(**atributos)


class FabricaProductoPerecedero(FabricaProducto):
    def crear(self, atributos, datos):
        return ProductoPerecedero(
            fecha_vencimiento=datos.get("fecha_vencimiento"), **atributos
        )


_FABRICA_GENERAL = FabricaProductoGeneral()
_FABRICA_PERECEDERO = FabricaProductoPerecedero()


def obtener_fabrica(datos):
    """Elige la fábrica según si los datos traen una fecha de vencimiento válida."""
    fecha = validadores.fecha_valida(datos.get("fecha_vencimiento"), "Fecha de vencimiento")
    return _FABRICA_PERECEDERO if fecha else _FABRICA_GENERAL


def crear_producto(datos):
    return obtener_fabrica(datos).construir(datos)
