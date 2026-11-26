from models.base import ModeloBase


class Modulo(ModeloBase):
    """Opción del menú lateral asociada a una ruta de la SPA."""

    def __init__(self, id_modulo, nombre, icono, ruta, orden=0, estado=1):
        self.id_modulo = id_modulo
        self.nombre = nombre
        self.icono = icono
        self.ruta = ruta
        self.orden = orden
        self.estado = estado

    def to_dict(self):
        """Representación del módulo para las respuestas JSON."""
        return {
            "id_modulo": self.id_modulo,
            "nombre": self.nombre,
            "icono": self.icono,
            "ruta": self.ruta,
            "orden": self.orden,
        }


def crear_modulo(datos):
    """Construye un módulo a partir de una fila de la base de datos."""
    return Modulo(
        id_modulo=datos.get("id_modulo"),
        nombre=datos.get("nombre"),
        icono=datos.get("icono"),
        ruta=datos.get("ruta"),
        orden=int(datos.get("orden", 0)),
        estado=int(datos.get("estado", 1)),
    )
