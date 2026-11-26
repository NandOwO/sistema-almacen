import validadores
from models.base import ModeloBase


class Categoria(ModeloBase):
    """Agrupación de productos del catálogo."""

    def __init__(self, id, nombre, descripcion=None, estado=1):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = int(estado)
        self.validar()

    def validar(self):
        """Valida y normaliza los campos de la categoría."""
        self.nombre = validadores.texto_general(self.nombre, "Nombre de la categoría", maximo=80)

    def to_dict(self):
        """Representación de la categoría para las respuestas JSON."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
        }


def crear_categoria(datos):
    """Construye una categoría a partir de un diccionario."""
    return Categoria(
        id=datos.get("id"),
        nombre=(datos.get("nombre") or "").strip(),
        descripcion=(datos.get("descripcion") or None),
        estado=int(datos.get("estado", 1)),
    )
