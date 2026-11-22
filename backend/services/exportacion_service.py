from collections import namedtuple

from exceptions.errores import DatosInvalidosError
from patterns.estrategias_exportacion import ExportacionExcel, ExportacionPDF

ArchivoExportado = namedtuple("ArchivoExportado", "contenido nombre tipo_mime")


class ExportacionService:
    """Contexto del patrón Strategy: delega la generación en la estrategia del formato."""

    def __init__(self, estrategias=None):
        self._estrategias = estrategias or {
            "excel": ExportacionExcel(),
            "pdf": ExportacionPDF(),
        }

    @property
    def formatos(self):
        return tuple(self._estrategias)

    def obtener_estrategia(self, formato):
        estrategia = self._estrategias.get(formato)
        if estrategia is None:
            opciones = ", ".join(f"'{f}'" for f in self.formatos)
            raise DatosInvalidosError(f"Formato inválido (use {opciones}).")
        return estrategia

    def exportar(self, formato, nombre, titulo, tablas):
        estrategia = self.obtener_estrategia(formato)
        return ArchivoExportado(
            contenido=estrategia.exportar(titulo, tablas),
            nombre=f"{nombre}.{estrategia.extension}",
            tipo_mime=estrategia.tipo_mime,
        )
