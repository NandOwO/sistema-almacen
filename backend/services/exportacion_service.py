from collections import namedtuple

from exceptions.errores import DatosInvalidosError
from patterns.estrategias_exportacion import (
    ExportacionCSV, ExportacionExcel, ExportacionJSON, ExportacionPDF,
)

ArchivoExportado = namedtuple("ArchivoExportado", "contenido nombre tipo_mime")


class ExportacionService:
    """Contexto del patrón Strategy: delega la generación en la estrategia del formato."""

    def __init__(self, estrategias=None):
        self._estrategias = estrategias or {
            "excel": ExportacionExcel(),
            "pdf": ExportacionPDF(),
            "csv": ExportacionCSV(),
            "json": ExportacionJSON(),
        }

    @property
    def formatos(self):
        """Formatos de exportación disponibles."""
        return tuple(self._estrategias)

    def obtener_estrategia(self, formato):
        """Devuelve la estrategia del formato o lanza un error si no existe."""
        estrategia = self._estrategias.get(formato)
        if estrategia is None:
            opciones = ", ".join(f"'{f}'" for f in self.formatos)
            raise DatosInvalidosError(f"Formato inválido (use {opciones}).")
        return estrategia

    def exportar(self, formato, nombre, titulo, tablas):
        """Genera el archivo con la estrategia del formato y le pone nombre y tipo MIME."""
        estrategia = self.obtener_estrategia(formato)
        return ArchivoExportado(
            contenido=estrategia.exportar(titulo, tablas),
            nombre=f"{nombre}.{estrategia.extension}",
            tipo_mime=estrategia.tipo_mime,
        )
