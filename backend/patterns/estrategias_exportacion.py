import io
from abc import ABC, abstractmethod

import pandas as pd
from fpdf import FPDF
from openpyxl.utils import get_column_letter

ANCHO_MINIMO_COLUMNA = 8
ANCHO_MAXIMO_COLUMNA = 40
LARGO_MAXIMO_CELDA_PDF = 22


class EstrategiaExportacion(ABC):
    """Estrategia del patrón Strategy: un formato de archivo para los reportes."""

    extension = ""
    tipo_mime = ""

    @abstractmethod
    def exportar(self, titulo, tablas):
        """Genera el archivo a partir de [(subtitulo, DataFrame)] y lo devuelve en memoria."""


class ExportacionExcel(EstrategiaExportacion):
    extension = "xlsx"
    tipo_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def exportar(self, titulo, tablas):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for nombre, df in tablas:
                hoja = nombre[:31]
                df.to_excel(writer, sheet_name=hoja, index=False)
                self._ajustar_anchos(writer.sheets[hoja], df)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _ajustar_anchos(hoja, df):
        for i, columna in enumerate(df.columns, start=1):
            largo = max([len(str(columna)), ANCHO_MINIMO_COLUMNA] + [len(str(v)) for v in df[columna]])
            hoja.column_dimensions[get_column_letter(i)].width = min(largo + 3, ANCHO_MAXIMO_COLUMNA)


class ExportacionPDF(EstrategiaExportacion):
    extension = "pdf"
    tipo_mime = "application/pdf"

    def exportar(self, titulo, tablas):
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 10, self._latin1(titulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, self._latin1("Sistema de Inventario · reporte generado automáticamente"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(20, 20, 20)
        pdf.ln(3)

        for subtitulo, df in tablas:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, self._latin1(subtitulo), new_x="LMARGIN", new_y="NEXT")
            self._tabla(pdf, df)
            pdf.ln(5)

        return io.BytesIO(bytes(pdf.output()))

    @staticmethod
    def _latin1(texto):
        return str(texto).encode("latin-1", "replace").decode("latin-1")

    @staticmethod
    def _formato_celda(valor):
        if isinstance(valor, float):
            return f"{valor:,.2f}"
        return "" if valor is None else str(valor)

    def _tabla(self, pdf, df):
        columnas = list(df.columns)
        if not columnas:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 7, self._latin1("Sin datos."), new_x="LMARGIN", new_y="NEXT")
            return

        ancho = (pdf.w - 2 * pdf.l_margin) / len(columnas)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(235, 237, 240)
        for col in columnas:
            pdf.cell(ancho, 7, self._latin1(col)[:LARGO_MAXIMO_CELDA_PDF], border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for _, fila in df.iterrows():
            for col in columnas:
                texto = self._latin1(self._formato_celda(fila[col]))[:LARGO_MAXIMO_CELDA_PDF]
                pdf.cell(ancho, 6, texto, border=1)
            pdf.ln()
