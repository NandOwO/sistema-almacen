from abc import ABC, abstractmethod

ESTADO_INACTIVO = 0
ESTADO_ACTIVO = 1
ESTADO_ELIMINADO = 2
ESTADOS_VALIDOS = (ESTADO_INACTIVO, ESTADO_ACTIVO, ESTADO_ELIMINADO)


class ModeloBase(ABC):
    """Contrato común de las entidades del dominio."""

    def validar(self):
        """Reglas que involucran varios atributos; por defecto no exige ninguna."""

    @abstractmethod
    def to_dict(self):
        """Representación serializable de la entidad."""

    def __repr__(self):
        return f"{type(self).__name__}({self.to_dict()!r})"
