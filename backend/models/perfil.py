import validadores
from models.base import ModeloBase

NOMBRE_PERFIL_ADMIN = "Administrador"


class Perfil(ModeloBase):
    """Rol de usuario con la lista de módulos que puede usar."""

    def __init__(self, id_perfil, nombre, descripcion=None, modulos=None, estado=1):
        self.id_perfil = id_perfil
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = int(estado)

        self.modulos = [int(m) for m in (modulos or [])]
        self.validar()

    @property
    def es_sistema(self):
        """True si es el perfil Administrador, que el sistema protege de cambios."""
        return (self.nombre or "").lower() == NOMBRE_PERFIL_ADMIN.lower()

    def validar(self):
        """Valida y normaliza los campos del perfil."""
        self.nombre = validadores.texto_sin_simbolos(self.nombre, "Nombre del perfil", maximo=80)
        self.descripcion = validadores.texto_requerido(
            self.descripcion, "Descripción", maximo=200
        ) if (self.descripcion or "").strip() else None

    def to_dict(self):
        """Representación del perfil para las respuestas JSON."""
        return {
            "id_perfil": self.id_perfil,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "modulos": self.modulos,
            "es_sistema": self.es_sistema,
        }


def crear_perfil(datos):
    """Construye un perfil a partir de un diccionario."""
    return Perfil(
        id_perfil=datos.get("id_perfil"),
        nombre=datos.get("nombre"),
        descripcion=datos.get("descripcion"),
        modulos=datos.get("modulos") or [],
        estado=int(datos.get("estado", 1)),
    )
